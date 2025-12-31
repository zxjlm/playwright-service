#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-26 10:29:50
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""
import asyncio
import base64
import json
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import AsyncGenerator, Literal, Optional, Union
from loguru import logger
from patchright.async_api import (
    Page,
    Response,
    TimeoutError as PWTimeoutError,
    ProxySettings,
    BrowserContext,
)
from base_proxy import proxy_pool, is_proxy_error
from get_error import get_error
from schemas.service_schema import (
    BaseBrowserInput,
    HtmlResponse,
    ScreenshotInput,
    ScreenshotResponse,
    UrlInput,
)
from models.request_history_model import RequestHistoryModel
from config import request_semaphore, service_config
from browsers import browser_manager
from encoding_utils import create_encoding_route_handler
from apis.metrics import (
    browser_operations_total,
    browser_operation_duration_seconds,
    browser_operations_status_total,
    browser_page_status_codes_total,
    cache_operations_total,
    waiting_requests,
    processing_requests,
    proxy_usage_total,
    proxy_failures_total,
    errors_total,
    browser_reinitializations_total,
    proxy_retry_total,
)

# Maximum number of proxy retry attempts
MAX_PROXY_RETRY_ATTEMPTS = 3


@dataclass
class BrowserSession:
    """Browser session context holding page, context and response info."""

    page: Page
    context: BrowserContext
    response: Optional[Response] = None
    response_headers: str = ""
    request_headers: str = ""
    start_time: float = field(default_factory=time.perf_counter)


def _should_reinit_browser(exc: Exception) -> bool:
    """Detect browser/context closed errors that require reinit."""
    message = str(exc)
    return "has been closed" in message or "browser has been closed" in message


async def _get_proxy_settings(force_refresh: bool = False) -> Optional[ProxySettings]:
    """
    Get proxy settings using the proxy pool (with reuse support).
    
    Args:
        force_refresh: If True, force fetching a new proxy instead of reusing cached one
        
    Returns:
        ProxySettings or None
    """
    proxy_type = service_config.proxy_type
    proxy_usage_total.labels(proxy_type=proxy_type).inc()

    try:
        proxy = await proxy_pool.get_proxy(force_refresh=force_refresh)
        return ProxySettings(server=proxy) if proxy else None
    except Exception as e:
        logger.error(f"Failed to get proxy: {e}")
        proxy_failures_total.inc()
        errors_total.labels(error_type="proxy_error").inc()
        return None


async def _create_browser_page(
    browser_type: str, proxy_item: Optional[ProxySettings]
) -> tuple[Page, BrowserContext]:
    """Create browser page with retry logic for stale browsers."""
    page: Optional[Page] = None
    context: Optional[BrowserContext] = None

    for attempt in range(2):
        browser_instance = await browser_manager.get_browser(browser_type, headless=True)
        try:
            context = await browser_instance.create_context(proxy_item)
            page = await browser_instance.create_page(context)
            break
        except Exception as exc:
            if attempt == 0 and _should_reinit_browser(exc):
                logger.warning(
                    f"Browser stale detected, reinitializing {browser_type}: {exc}"
                )
                browser_reinitializations_total.labels(browser_type=browser_type).inc()
                await browser_manager.cleanup_all_browsers()
                continue
            raise

    if page is None or context is None:
        raise RuntimeError("Failed to create browser context/page")

    return page, context


async def _setup_page(
    page: Page,
    browser_input: BaseBrowserInput,
    viewport_size: Optional[dict] = None,
) -> None:
    """
    Set up page with viewport, encoding handler, and headers.
    
    Args:
        page: The page to set up
        browser_input: Input parameters
        viewport_size: Optional viewport size
    """
    # Set viewport size if specified (for screenshots)
    if viewport_size:
        await page.set_viewport_size(viewport_size)

    # Set up encoding route handler to fix non-UTF-8 encoded pages
    await create_encoding_route_handler(page)

    # Set extra HTTP headers if provided
    if browser_input.headers:
        await page.set_extra_http_headers(browser_input.headers)


@asynccontextmanager
async def browser_session(
    browser_input: BaseBrowserInput,
    operation: Literal["html", "screenshot"],
    viewport_size: Optional[dict] = None,
    force_new_proxy: bool = False,
) -> AsyncGenerator[BrowserSession, None]:
    """
    Async context manager for browser sessions.

    Handles common browser operations:
    - Waiting request logging
    - Proxy acquisition (with reuse support)
    - Browser instance creation with retry
    - Page setup (encoding, headers, viewport)
    - Resource cleanup

    Note: Navigation (page.goto) should be handled by the caller to allow
    proper timeout error handling.

    Args:
        browser_input: Input parameters (UrlInput or ScreenshotInput)
        operation: Operation type for logging
        viewport_size: Optional viewport size for screenshots
        force_new_proxy: If True, force fetching a new proxy

    Yields:
        BrowserSession with page, context (response will be None initially)
    """
    waiting_count = get_waiting_requests()
    if waiting_count > 0:
        logger.info(
            f"{operation.capitalize()} request for {browser_input.url} is waiting. "
            f"Current waiting requests: {waiting_count}"
        )

    proxy_item = await _get_proxy_settings(force_refresh=force_new_proxy)

    async with request_semaphore:
        logger.info(
            f"Received {operation} request for URL: {browser_input.url} "
            f"using browser: {browser_input.browser_type}"
        )

        page, context = await _create_browser_page(
            browser_input.browser_type, proxy_item
        )

        try:
            await _setup_page(page, browser_input, viewport_size)

            logger.debug(
                f"Created new {browser_input.browser_type} page for {operation}"
            )

            session = BrowserSession(
                page=page,
                context=context,
                response=None,
            )

            yield session

        finally:
            if page:
                await page.close()
            if context:
                await context.close()


async def recreate_session_with_new_proxy(
    browser_input: BaseBrowserInput,
    operation: Literal["html", "screenshot"],
    viewport_size: Optional[dict] = None,
    old_page: Optional[Page] = None,
    old_context: Optional[BrowserContext] = None,
) -> tuple[Page, BrowserContext]:
    """
    Recreate browser session with a new proxy.
    
    This function is used when a proxy error is detected and we need to
    switch to a new proxy. It closes the old page/context and creates new ones.
    
    Args:
        browser_input: Input parameters
        operation: Operation type for logging
        viewport_size: Optional viewport size
        old_page: Previous page to close
        old_context: Previous context to close
        
    Returns:
        Tuple of (new_page, new_context)
    """
    # Close old resources
    if old_page:
        try:
            await old_page.close()
        except Exception as e:
            logger.debug(f"Error closing old page: {e}")
    if old_context:
        try:
            await old_context.close()
        except Exception as e:
            logger.debug(f"Error closing old context: {e}")
    
    # Get new proxy (force refresh)
    proxy_item = await _get_proxy_settings(force_refresh=True)
    
    # Create new page and context
    page, context = await _create_browser_page(
        browser_input.browser_type, proxy_item
    )
    
    # Set up the new page
    await _setup_page(page, browser_input, viewport_size)
    
    logger.info(
        f"Recreated {browser_input.browser_type} session with new proxy for {operation}"
    )
    
    return page, context


class ProxyError(Exception):
    """Exception raised when a proxy error is detected."""
    
    def __init__(self, message: str, reason: str, original_error: Exception):
        super().__init__(message)
        self.reason = reason
        self.original_error = original_error


async def navigate_page(
    session: BrowserSession,
    url: str,
    timeout: int,
    wait_until: str,
) -> Response:
    """
    Navigate to a URL and update the session with response info.
    
    If a proxy error is detected (net::ERR_TUNNEL_CONNECTION_FAILED or 
    NS_ERROR_PROXY_CONNECTION_REFUSED), it raises a ProxyError to signal
    that the caller should retry with a new proxy.

    Args:
        session: The browser session
        url: URL to navigate to
        timeout: Navigation timeout in milliseconds
        wait_until: Wait until condition

    Returns:
        The response object
        
    Raises:
        ProxyError: If a proxy-related error is detected
    """
    logger.debug(f"Navigating to URL: {url}")
    try:
        response = await session.page.goto(
            url,
            timeout=timeout,
            wait_until=wait_until,
        )
        assert response

        session.response = response
        session.response_headers = json.dumps(response.headers)
        session.request_headers = json.dumps(response.request.headers)

        return response
    except PWTimeoutError as e:
        # logger.warning(f"Page load timeout: {e}, {url}")
        raise e
    except Exception as e:
        # Check if this is a proxy error
        is_proxy_err, reason = is_proxy_error(e)
        if is_proxy_err:
            logger.warning(f"Proxy error detected: {e} (reason: {reason})")
            raise ProxyError(
                f"Proxy error during navigation: {e}",
                reason=reason,
                original_error=e,
            )
        # Re-raise non-proxy errors
        raise


def _get_operation_status(status_code: Union[int, str]) -> str:
    """Determine operation status from status code."""
    status_code_int = (
        int(status_code)
        if isinstance(status_code, (int, str)) and str(status_code).isdigit()
        else 0
    )
    return "success" if 200 <= status_code_int < 400 else "failure"


async def record_operation_metrics(
    browser_type: str,
    operation: str,
    result_status_code: Union[int, str],
    operation_start_time: float,
    url: str,
    request_body: str,
    response_time: float,
    response_headers: str,
    response_body: str,
    request_headers: str,
    session,
) -> None:
    """Record Prometheus metrics and request history for browser operations."""
    operation_duration = time.perf_counter() - operation_start_time

    # Record browser operation metrics
    browser_operations_total.labels(
        browser_type=browser_type, operation=operation
    ).inc()
    browser_operation_duration_seconds.labels(
        browser_type=browser_type, operation=operation
    ).observe(operation_duration)

    # Record operation status
    status = _get_operation_status(result_status_code)
    browser_operations_status_total.labels(
        browser_type=browser_type, operation=operation, status=status
    ).inc()

    # Record page status code if valid
    status_code_int = (
        int(result_status_code)
        if isinstance(result_status_code, (int, str))
        and str(result_status_code).isdigit()
        else 0
    )
    if status_code_int > 0:
        browser_page_status_codes_total.labels(
            browser_type=browser_type,
            operation=operation,
            page_status_code=str(result_status_code),
        ).inc()

    # Decrease processing request count
    processing_requests.dec()

    # Create request history record
    await RequestHistoryModel.create_request_history(
        url=url,
        browser_type=browser_type,
        status_code=result_status_code,
        response_time=response_time,
        response_headers=response_headers,
        response_body=response_body,
        request_headers=request_headers,
        request_body=request_body,
        session=session,
    )


def get_waiting_requests() -> int:
    if request_semaphore._waiters:
        count = len(request_semaphore._waiters)
        # 更新 Prometheus 指标
        waiting_requests.set(count)
        return count
    else:
        waiting_requests.set(0)
        return 0


async def force_get_content(
    page: Page, url: str
) -> tuple[str | None, Exception | None]:
    html_content = None
    last_error = None
    # retry mechanism: wait for the page to be stable before reading the content
    for attempt in range(3):
        try:
            # short wait for the page to be stable, avoid reading the content during navigation
            await asyncio.sleep(0.5)
            # try to wait for the DOM to be loaded
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=2000)
            except Exception:
                pass  # ignore the timeout error, continue to try to get the content
            html_content = await page.content()
            if html_content and len(html_content) > 5000:
                break
        except Exception as retry_e:
            last_error = retry_e
            logger.debug(
                f"Attempt {attempt + 1} to read content failed: {retry_e}, {url}"
            )

    return html_content, last_error


async def _handle_html_navigation(
    bs: BrowserSession,
    url_input: UrlInput,
    browser_type: str,
    operation: str,
) -> tuple[HtmlResponse, str, str]:
    """
    Handle the HTML navigation and content retrieval.
    
    Args:
        bs: Browser session
        url_input: URL input parameters
        browser_type: Browser type
        operation: Operation type
        
    Returns:
        Tuple of (result, response_headers, request_headers)
        
    Raises:
        ProxyError: If a proxy error is detected
    """
    response = await navigate_page(
        bs,
        str(url_input.url),
        url_input.timeout,
        url_input.wait_until,
    )
    response_headers = bs.response_headers
    request_headers = bs.request_headers

    logger.debug(f"Page loaded, waiting for stability: {url_input.url}")
    await asyncio.sleep(1)

    try:
        await bs.page.wait_for_load_state("domcontentloaded", timeout=2000)
    except Exception as e_:
        logger.warning(f"Page load timeout: {e_}, {url_input.url}")

    html = await bs.page.content()
    logger.debug(f"Page content retrieved successfully: {url_input.url}")

    result = HtmlResponse(
        html=html,
        page_status_code=response.status,
        page_error=get_error(response.status),
    )
    # Record page status code
    browser_page_status_codes_total.labels(
        browser_type=browser_type,
        operation=operation,
        page_status_code=response.status,
    ).inc()
    
    return result, response_headers, request_headers


async def get_html_base(url_input: UrlInput, session) -> HtmlResponse:
    """
    Fetch HTML content from a URL using a browser.
    
    Supports proxy retry: if a proxy error is detected (net::ERR_TUNNEL_CONNECTION_FAILED
    or NS_ERROR_PROXY_CONNECTION_REFUSED), the function will automatically switch to a
    new proxy and retry, up to MAX_PROXY_RETRY_ATTEMPTS times.
    """
    response_time = 0.0
    response_headers = ""
    response_body = ""
    request_headers = ""
    request_body = url_input.model_dump_json()
    result = HtmlResponse(html="", page_status_code=-1, page_error="")
    browser_type = url_input.browser_type
    operation = "html"
    operation_start_time = time.perf_counter()

    # Update processing request count
    processing_requests.inc()

    # Check cache first
    if url_input.use_cache:
        request_history = await RequestHistoryModel.get_request_history(
            url_input.url, url_input.browser_type, session
        )
        if request_history:
            cache_operations_total.labels(status="hit").inc()
            processing_requests.dec()
            return HtmlResponse(
                html=request_history.response_body,
                page_status_code=request_history.status_code,
                page_error="",
                cache_hit=1,
            )
        else:
            cache_operations_total.labels(status="miss").inc()

    try:
        waiting_count = get_waiting_requests()
        if waiting_count > 0:
            logger.info(
                f"{operation.capitalize()} request for {url_input.url} is waiting. "
                f"Current waiting requests: {waiting_count}"
            )

        proxy_item = await _get_proxy_settings(force_refresh=False)

        async with request_semaphore:
            logger.info(
                f"Received {operation} request for URL: {url_input.url} "
                f"using browser: {url_input.browser_type}"
            )

            page, context = await _create_browser_page(
                url_input.browser_type, proxy_item
            )
            start_time = time.perf_counter()

            try:
                await _setup_page(page, url_input, None)

                logger.debug(
                    f"Created new {url_input.browser_type} page for {operation}"
                )

                bs = BrowserSession(
                    page=page,
                    context=context,
                    response=None,
                    start_time=start_time,
                )

                # Proxy retry loop
                proxy_retry_count = 0
                last_proxy_error: Optional[ProxyError] = None
                
                while proxy_retry_count < MAX_PROXY_RETRY_ATTEMPTS:
                    try:
                        result, response_headers, request_headers = await _handle_html_navigation(
                            bs, url_input, browser_type, operation
                        )
                        response_body = result.html
                        break  # Success, exit retry loop
                        
                    except ProxyError as pe:
                        proxy_retry_count += 1
                        last_proxy_error = pe
                        proxy_retry_total.labels(attempt=str(proxy_retry_count)).inc()
                        
                        logger.warning(
                            f"Proxy error on attempt {proxy_retry_count}/{MAX_PROXY_RETRY_ATTEMPTS}: "
                            f"{pe} for URL: {url_input.url}"
                        )
                        
                        # Invalidate the current proxy
                        await proxy_pool.invalidate_proxy(reason=pe.reason)
                        
                        if proxy_retry_count < MAX_PROXY_RETRY_ATTEMPTS:
                            # Recreate session with new proxy
                            page, context = await recreate_session_with_new_proxy(
                                url_input, operation, None, page, context
                            )
                            bs = BrowserSession(
                                page=page,
                                context=context,
                                response=None,
                                start_time=start_time,
                            )
                            logger.info(
                                f"Retrying with new proxy (attempt {proxy_retry_count + 1})"
                            )
                        else:
                            # Max retries reached
                            errors_total.labels(error_type="proxy_error").inc()
                            result = HtmlResponse(
                                html="",
                                page_status_code=604,
                                page_error=f"Proxy error after {MAX_PROXY_RETRY_ATTEMPTS} retries: {pe}",
                            )
                            
                    except PWTimeoutError as e:
                        errors_total.labels(error_type="timeout").inc()
                        logger.warning(f"Page load timeout: {e}, {url_input.url}")
                        await asyncio.sleep(0.5)

                        if url_input.is_force_get_content:
                            try:
                                html_content, last_error = await force_get_content(
                                    bs.page, url_input.url
                                )
                                if html_content and len(html_content) > 5000:
                                    result = HtmlResponse(
                                        html=html_content,
                                        page_status_code=600 if not last_error else 601,
                                        page_error=(
                                            f"page load timeout, {e}"
                                            if not last_error
                                            else f"page load failed while force read content, {last_error}"
                                        ),
                                    )
                            except Exception as force_e:
                                logger.warning(
                                    f"Error occurred while force read content: {force_e}, {url_input.url}"
                                )
                                result = HtmlResponse(
                                    html="",
                                    page_status_code=601,
                                    page_error=f"page load failed while force read content, {force_e}",
                                )
                        else:
                            result = HtmlResponse(
                                html="",
                                page_status_code=601,
                                page_error=f"page load timeout, {e}",
                            )
                        break  # Exit retry loop on timeout

                    except Exception as e:
                        # Check if it's a proxy error that wasn't caught by navigate_page
                        is_proxy_err, reason = is_proxy_error(e)
                        if is_proxy_err:
                            proxy_retry_count += 1
                            proxy_retry_total.labels(attempt=str(proxy_retry_count)).inc()
                            
                            logger.warning(
                                f"Proxy error on attempt {proxy_retry_count}/{MAX_PROXY_RETRY_ATTEMPTS}: "
                                f"{e} for URL: {url_input.url}"
                            )
                            
                            await proxy_pool.invalidate_proxy(reason=reason)
                            
                            if proxy_retry_count < MAX_PROXY_RETRY_ATTEMPTS:
                                page, context = await recreate_session_with_new_proxy(
                                    url_input, operation, None, page, context
                                )
                                bs = BrowserSession(
                                    page=page,
                                    context=context,
                                    response=None,
                                    start_time=start_time,
                                )
                                logger.info(
                                    f"Retrying with new proxy (attempt {proxy_retry_count + 1})"
                                )
                                continue
                            else:
                                errors_total.labels(error_type="proxy_error").inc()
                                result = HtmlResponse(
                                    html="",
                                    page_status_code=604,
                                    page_error=f"Proxy error after {MAX_PROXY_RETRY_ATTEMPTS} retries: {e}",
                                )
                        else:
                            logger.error(f"Error occurred while loading page: {e}, {url_input.url}")
                            errors_total.labels(error_type="browser_error").inc()
                            result = HtmlResponse(
                                html="", page_status_code=602, page_error=f"page load failed, {e}"
                            )
                        break  # Exit retry loop on non-proxy error

                response_time = time.perf_counter() - start_time

            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        errors_total.labels(error_type="other").inc()
        result = HtmlResponse(
            html="", page_status_code=603, page_error=f"request failed, {e}"
        )

    finally:
        await record_operation_metrics(
            browser_type=browser_type,
            operation=operation,
            result_status_code=result.page_status_code,
            operation_start_time=operation_start_time,
            url=str(url_input.url),
            request_body=request_body,
            response_time=response_time,
            response_headers=response_headers,
            response_body=response_body,
            request_headers=request_headers,
            session=session,
        )

    return result


async def _handle_screenshot_navigation(
    bs: BrowserSession,
    screenshot_input: ScreenshotInput,
    browser_type: str,
    operation: str,
) -> tuple[ScreenshotResponse, str, str]:
    """
    Handle the screenshot navigation and capture.
    
    Args:
        bs: Browser session
        screenshot_input: Screenshot input parameters
        browser_type: Browser type
        operation: Operation type
        
    Returns:
        Tuple of (result, response_headers, request_headers)
        
    Raises:
        ProxyError: If a proxy error is detected
    """
    response = await navigate_page(
        bs,
        str(screenshot_input.url),
        screenshot_input.timeout,
        screenshot_input.wait_until,
    )
    response_headers = bs.response_headers
    request_headers = bs.request_headers

    logger.debug(
        f"Page loaded, waiting for screenshot: {screenshot_input.url}"
    )
    await asyncio.sleep(2)

    # Take screenshot
    screenshot_options = {}
    if screenshot_input.full_page:
        screenshot_options["full_page"] = True

    screenshot_bytes = await bs.page.screenshot(**screenshot_options)
    logger.debug(f"Screenshot taken successfully: {screenshot_input.url}")

    # Encode screenshot to base64 for JSON serialization
    screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

    result = ScreenshotResponse(
        screenshot=screenshot_base64,
        page_status_code=response.status,
        page_error=get_error(response.status),
    )
    # Record page status code
    browser_page_status_codes_total.labels(
        browser_type=browser_type,
        operation=operation,
        page_status_code=response.status,
    ).inc()
    
    return result, response_headers, request_headers


async def get_html_screenshot(
    screenshot_input: ScreenshotInput, session
) -> ScreenshotResponse:
    """
    Take a screenshot of a URL using a browser.
    
    Supports proxy retry: if a proxy error is detected (net::ERR_TUNNEL_CONNECTION_FAILED
    or NS_ERROR_PROXY_CONNECTION_REFUSED), the function will automatically switch to a
    new proxy and retry, up to MAX_PROXY_RETRY_ATTEMPTS times.
    """
    response_time = 0.0
    response_headers = ""
    response_body = ""
    request_headers = ""
    request_body = screenshot_input.model_dump_json()
    result = ScreenshotResponse(screenshot="", page_status_code=-1, page_error="")
    browser_type = screenshot_input.browser_type
    operation = "screenshot"
    operation_start_time = time.perf_counter()

    # Update processing request count
    processing_requests.inc()

    viewport_size = {
        "width": screenshot_input.width,
        "height": screenshot_input.height,
    }

    try:
        waiting_count = get_waiting_requests()
        if waiting_count > 0:
            logger.info(
                f"{operation.capitalize()} request for {screenshot_input.url} is waiting. "
                f"Current waiting requests: {waiting_count}"
            )

        proxy_item = await _get_proxy_settings(force_refresh=False)

        async with request_semaphore:
            logger.info(
                f"Received {operation} request for URL: {screenshot_input.url} "
                f"using browser: {screenshot_input.browser_type}"
            )

            page, context = await _create_browser_page(
                screenshot_input.browser_type, proxy_item
            )
            start_time = time.perf_counter()

            try:
                await _setup_page(page, screenshot_input, viewport_size)

                logger.debug(
                    f"Created new {screenshot_input.browser_type} page for {operation}"
                )

                bs = BrowserSession(
                    page=page,
                    context=context,
                    response=None,
                    start_time=start_time,
                )

                # Proxy retry loop
                proxy_retry_count = 0
                
                while proxy_retry_count < MAX_PROXY_RETRY_ATTEMPTS:
                    try:
                        result, response_headers, request_headers = await _handle_screenshot_navigation(
                            bs, screenshot_input, browser_type, operation
                        )
                        break  # Success, exit retry loop
                        
                    except ProxyError as pe:
                        proxy_retry_count += 1
                        proxy_retry_total.labels(attempt=str(proxy_retry_count)).inc()
                        
                        logger.warning(
                            f"Proxy error on attempt {proxy_retry_count}/{MAX_PROXY_RETRY_ATTEMPTS}: "
                            f"{pe} for URL: {screenshot_input.url}"
                        )
                        
                        # Invalidate the current proxy
                        await proxy_pool.invalidate_proxy(reason=pe.reason)
                        
                        if proxy_retry_count < MAX_PROXY_RETRY_ATTEMPTS:
                            # Recreate session with new proxy
                            page, context = await recreate_session_with_new_proxy(
                                screenshot_input, operation, viewport_size, page, context
                            )
                            bs = BrowserSession(
                                page=page,
                                context=context,
                                response=None,
                                start_time=start_time,
                            )
                            logger.info(
                                f"Retrying with new proxy (attempt {proxy_retry_count + 1})"
                            )
                        else:
                            # Max retries reached
                            errors_total.labels(error_type="proxy_error").inc()
                            result = ScreenshotResponse(
                                screenshot="",
                                page_status_code=604,
                                page_error=f"Proxy error after {MAX_PROXY_RETRY_ATTEMPTS} retries: {pe}",
                            )
                            
                    except PWTimeoutError as e:
                        errors_total.labels(error_type="timeout").inc()
                        logger.warning(
                            f"Page load timeout for screenshot: {e}, {screenshot_input.url}"
                        )

                        if screenshot_input.is_force_get_content:
                            try:
                                # Try to take screenshot even if page load timeout
                                screenshot_options = {}
                                if screenshot_input.full_page:
                                    screenshot_options["full_page"] = True
                                screenshot_bytes = await bs.page.screenshot(**screenshot_options)
                                screenshot_base64 = base64.b64encode(screenshot_bytes).decode(
                                    "utf-8"
                                )
                                result = ScreenshotResponse(
                                    screenshot=screenshot_base64,
                                    page_status_code=600,
                                    page_error=f"page load timeout, {e}",
                                )
                            except Exception as force_e:
                                logger.warning(
                                    f"Error occurred while force taking screenshot: {force_e}, {screenshot_input.url}"
                                )
                                result = ScreenshotResponse(
                                    screenshot="",
                                    page_status_code=601,
                                    page_error=f"page load failed while force taking screenshot, {force_e}",
                                )
                        else:
                            result = ScreenshotResponse(
                                screenshot="",
                                page_status_code=601,
                                page_error=f"page load timeout, {e}",
                            )
                        break  # Exit retry loop on timeout

                    except Exception as e:
                        # Check if it's a proxy error that wasn't caught by navigate_page
                        is_proxy_err, reason = is_proxy_error(e)
                        if is_proxy_err:
                            proxy_retry_count += 1
                            proxy_retry_total.labels(attempt=str(proxy_retry_count)).inc()
                            
                            logger.warning(
                                f"Proxy error on attempt {proxy_retry_count}/{MAX_PROXY_RETRY_ATTEMPTS}: "
                                f"{e} for URL: {screenshot_input.url}"
                            )
                            
                            await proxy_pool.invalidate_proxy(reason=reason)
                            
                            if proxy_retry_count < MAX_PROXY_RETRY_ATTEMPTS:
                                page, context = await recreate_session_with_new_proxy(
                                    screenshot_input, operation, viewport_size, page, context
                                )
                                bs = BrowserSession(
                                    page=page,
                                    context=context,
                                    response=None,
                                    start_time=start_time,
                                )
                                logger.info(
                                    f"Retrying with new proxy (attempt {proxy_retry_count + 1})"
                                )
                                continue
                            else:
                                errors_total.labels(error_type="proxy_error").inc()
                                result = ScreenshotResponse(
                                    screenshot="",
                                    page_status_code=604,
                                    page_error=f"Proxy error after {MAX_PROXY_RETRY_ATTEMPTS} retries: {e}",
                                )
                        else:
                            logger.exception(e)
                            logger.error(
                                f"Error occurred while loading page for screenshot: {e}, {screenshot_input.url}"
                            )
                            errors_total.labels(error_type="browser_error").inc()
                            result = ScreenshotResponse(
                                screenshot="",
                                page_status_code=602,
                                page_error=f"page load failed, {e}",
                            )
                        break  # Exit retry loop on non-proxy error

                response_time = time.perf_counter() - start_time

            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()

    except Exception as e:
        logger.error(f"Error processing screenshot request: {str(e)}")
        errors_total.labels(error_type="other").inc()
        result = ScreenshotResponse(
            screenshot="", page_status_code=603, page_error=f"request failed, {e}"
        )

    finally:
        await record_operation_metrics(
            browser_type=browser_type,
            operation=operation,
            result_status_code=result.page_status_code,
            operation_start_time=operation_start_time,
            url=str(screenshot_input.url),
            request_body=request_body,
            response_time=response_time,
            response_headers=response_headers,
            response_body=response_body,
            request_headers=request_headers,
            session=session,
        )

    return result
