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
from typing import Optional
from loguru import logger
from patchright.async_api import (
    Page,
    Response,
    TimeoutError as PWTimeoutError,
    ProxySettings,
)
from base_proxy import ProxyManager
from get_error import get_error
from schemas.service_schema import HtmlResponse, ScreenshotInput, ScreenshotResponse
from schemas.service_schema import UrlInput
from models.request_history_model import RequestHistoryModel
from config import request_semaphore, service_config
from browsers import browser_manager
from encoding_utils import decode_html_content, fix_garbled_html
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
)


def _should_reinit_browser(exc: Exception) -> bool:
    """Detect browser/context closed errors that require reinit."""
    message = str(exc)
    return "has been closed" in message or "browser has been closed" in message


def get_waiting_requests() -> int:
    if request_semaphore._waiters:
        count = len(request_semaphore._waiters)
        # 更新 Prometheus 指标
        waiting_requests.set(count)
        return count
    else:
        waiting_requests.set(0)
        return 0


async def get_content_with_encoding(
    page: Page, response: Response, url: str
) -> tuple[str, str]:
    """
    Get page content with proper encoding handling.
    
    This function tries to get the correct encoding from the response
    and decodes the content properly, which is important for non-UTF-8 
    websites (e.g., Chinese government websites using GBK/GB2312).
    
    Args:
        page: Playwright page object
        response: Playwright response object
        url: The URL being accessed
        
    Returns:
        Tuple of (html_content, encoding_used)
    """
    # Try to get raw response body and decode with proper encoding
    try:
        body = await response.body()
        content_type = response.headers.get("content-type", "")
        html_content, encoding = decode_html_content(body, content_type)
        logger.debug(f"Decoded content with encoding: {encoding}, url: {url}")
        return html_content, encoding
    except Exception as e:
        logger.debug(f"Failed to get response body, falling back to page.content(): {e}")
    
    # Fallback to page.content() and try to fix if garbled
    html_content = await page.content()
    
    # Check if content appears garbled and try to fix
    html_content = fix_garbled_html(html_content)
    
    return html_content, "utf-8"


async def force_get_content(
    page: Page, url: str, response: Optional[Response] = None
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
            
            # Use encoding-aware content retrieval if response is available
            if response:
                html_content, _ = await get_content_with_encoding(page, response, url)
            else:
                html_content = await page.content()
                html_content = fix_garbled_html(html_content)
            
            if html_content and len(html_content) > 5000:
                break
        except Exception as retry_e:
            last_error = retry_e
            logger.debug(
                f"Attempt {attempt + 1} to read content failed: {retry_e}, {url}"
            )

    return html_content, last_error


async def get_html_base(url_input: UrlInput, session) -> HtmlResponse:
    response_time = 0
    response_headers = ""
    response_body = ""
    request_headers = ""
    request_body = url_input.model_dump_json()
    result = HtmlResponse(html="", page_status_code=-1, page_error="")
    browser_type = url_input.browser_type
    operation = "html"
    operation_start_time = time.perf_counter()

    # 更新处理中请求数
    processing_requests.inc()

    if url_input.use_cache:
        request_history = await RequestHistoryModel.get_request_history(
            url_input.url, url_input.browser_type, session
        )
        if request_history:
            # 记录缓存命中
            cache_operations_total.labels(status="hit").inc()
            processing_requests.dec()
            return HtmlResponse(
                html=request_history.response_body,
                page_status_code=request_history.status_code,
                page_error="",
                cache_hit=1,
            )
        else:
            # 记录缓存未命中
            cache_operations_total.labels(status="miss").inc()

    try:
        waiting_count = get_waiting_requests()
        if waiting_count > 0:
            logger.info(
                f"Request for {url_input.url} is waiting. Current waiting requests: {waiting_count}"
            )

        # 记录代理使用情况
        proxy_type = service_config.proxy_type
        proxy_usage_total.labels(proxy_type=proxy_type).inc()

        try:
            proxy = await ProxyManager().get_proxy()
            proxy_item = ProxySettings(server=proxy) if proxy else None
        except Exception as e:
            logger.error(f"Failed to get proxy: {e}")
            proxy_failures_total.inc()
            errors_total.labels(error_type="proxy_error").inc()
            proxy = None
            proxy_item = None

        async with request_semaphore:
            page: Optional[Page] = None
            context = None
            logger.info(
                f"Received request for URL: {url_input.url} using browser: {url_input.browser_type}"
            )

            # retry once when browser is stale/closed
            for attempt in range(2):
                browser_instance = await browser_manager.get_browser(
                    url_input.browser_type, headless=True
                )
                try:
                    context = await browser_instance.create_context(proxy_item)
                    page = await browser_instance.create_page(context)
                    break
                except Exception as exc:
                    if attempt == 0 and _should_reinit_browser(exc):
                        logger.warning(
                            f"Browser stale detected, reinitializing {url_input.browser_type}: {exc}"
                        )
                        # 记录浏览器重新初始化
                        browser_reinitializations_total.labels(
                            browser_type=browser_type
                        ).inc()
                        await browser_manager.cleanup_all_browsers()
                        continue
                    raise
            if page is None or context is None:
                raise RuntimeError("Failed to create browser context/page")

            start_time = time.perf_counter()

            try:
                logger.debug(f"Created new {url_input.browser_type} page")
                if url_input.headers:
                    await page.set_extra_http_headers(url_input.headers)

                logger.debug(f"Navigating to URL: {url_input.url}")
                response = await page.goto(
                    str(url_input.url),
                    timeout=url_input.timeout,
                    wait_until=url_input.wait_until,
                )
                assert response

                logger.debug(f"Page loaded, waiting for 5 seconds: {url_input.url}")
                await asyncio.sleep(1)

                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=2000)
                except Exception as e_:
                    logger.warning(f"Page load timeout: {e_}, {url_input.url}")
                    pass  # ignore the timeout error

                # Use encoding-aware content retrieval for proper handling of 
                # non-UTF-8 websites (e.g., Chinese government sites using GBK)
                html, encoding = await get_content_with_encoding(
                    page, response, str(url_input.url)
                )
                response_body = html
                logger.debug(
                    f"Page content retrieved successfully with encoding {encoding}: {url_input.url}"
                )

                response_headers = json.dumps(response.headers)
                request_headers = json.dumps(response.request.headers)

                result = HtmlResponse(
                    html=html,
                    page_status_code=response.status,
                    page_error=get_error(response.status),
                )
                # 记录页面状态码
                browser_page_status_codes_total.labels(
                    browser_type=browser_type,
                    operation=operation,
                    page_status_code=response.status,
                ).inc()
            except PWTimeoutError as e:
                # 记录超时错误
                errors_total.labels(error_type="timeout").inc()
                logger.warning(f"Page load timeout: {e}, {url_input.url}")
                await asyncio.sleep(0.5)
                if url_input.is_force_get_content:
                    try:
                        html_content, last_error = await force_get_content(
                            page, url_input.url, response=None
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
                    except Exception as e:
                        logger.warning(
                            f"Error occurred while force read content: {e}, {url_input.url}"
                        )
                        result = HtmlResponse(
                            html="",
                            page_status_code=601,
                            page_error=f"page load failed while force read content, {e}",
                        )
                else:
                    result = HtmlResponse(
                        html="",
                        page_status_code=601,
                        page_error=f"page load timeout, {e}",
                    )

            except Exception as e:
                logger.error(f"Error occurred while loading page: {e}, {url_input.url}")
                # 记录浏览器错误
                errors_total.labels(error_type="browser_error").inc()
                result = HtmlResponse(
                    html="", page_status_code=602, page_error=f"page load failed, {e}"
                )
            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()

            end_time = time.perf_counter()
            response_time = end_time - start_time

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        # 记录其他错误
        errors_total.labels(error_type="other").inc()
        result = HtmlResponse(
            html="", page_status_code=603, page_error=f"request failed, {e}"
        )

    finally:
        # 计算操作持续时间
        operation_duration = time.perf_counter() - operation_start_time

        # 记录浏览器操作指标
        browser_operations_total.labels(
            browser_type=browser_type, operation=operation
        ).inc()
        browser_operation_duration_seconds.labels(
            browser_type=browser_type, operation=operation
        ).observe(operation_duration)

        # 记录操作状态
        status_code_int = (
            int(result.page_status_code)
            if isinstance(result.page_status_code, (int, str))
            and str(result.page_status_code).isdigit()
            else 0
        )
        if status_code_int >= 200 and status_code_int < 400:
            status = "success"
        else:
            status = "failure"
        browser_operations_status_total.labels(
            browser_type=browser_type, operation=operation, status=status
        ).inc()

        # 记录页面状态码（如果还没有记录）
        if status_code_int > 0:
            browser_page_status_codes_total.labels(
                browser_type=browser_type,
                operation=operation,
                page_status_code=str(result.page_status_code),
            ).inc()

        # 减少处理中请求数
        processing_requests.dec()

        await RequestHistoryModel.create_request_history(
            url=url_input.url,
            browser_type=url_input.browser_type,
            status_code=result.page_status_code,
            response_time=response_time,
            response_headers=response_headers,
            response_body=response_body,
            request_headers=request_headers,
            request_body=request_body,
            session=session,
        )

    return result


async def get_html_screenshot(
    screenshot_input: ScreenshotInput, session
) -> ScreenshotResponse:
    response_time = 0
    response_headers = ""
    response_body = ""
    request_headers = ""
    request_body = screenshot_input.model_dump_json()
    result = ScreenshotResponse(screenshot="", page_status_code=-1, page_error="")
    browser_type = screenshot_input.browser_type
    operation = "screenshot"
    operation_start_time = time.perf_counter()

    # 更新处理中请求数
    processing_requests.inc()

    try:
        waiting_count = get_waiting_requests()
        if waiting_count > 0:
            logger.info(
                f"Screenshot request for {screenshot_input.url} is waiting. Current waiting requests: {waiting_count}"
            )

        # 记录代理使用情况
        proxy_type = service_config.proxy_type
        proxy_usage_total.labels(proxy_type=proxy_type).inc()

        try:
            proxy = await ProxyManager().get_proxy()
            proxy_item = ProxySettings(server=proxy) if proxy else None
        except Exception as e:
            logger.error(f"Failed to get proxy: {e}")
            proxy_failures_total.inc()
            errors_total.labels(error_type="proxy_error").inc()
            proxy = None
            proxy_item = None

        async with request_semaphore:
            page: Optional[Page] = None
            context = None
            logger.info(
                f"Received screenshot request for URL: {screenshot_input.url} using browser: {screenshot_input.browser_type}"
            )

            # retry once when browser is stale/closed
            for attempt in range(2):
                browser_instance = await browser_manager.get_browser(
                    screenshot_input.browser_type, headless=True
                )
                try:
                    context = await browser_instance.create_context(proxy_item)
                    page = await browser_instance.create_page(context)
                    break
                except Exception as exc:
                    if attempt == 0 and _should_reinit_browser(exc):
                        logger.warning(
                            f"Browser stale detected, reinitializing {screenshot_input.browser_type}: {exc}"
                        )
                        # 记录浏览器重新初始化
                        browser_reinitializations_total.labels(
                            browser_type=browser_type
                        ).inc()
                        await browser_manager.cleanup_all_browsers()
                        continue
                    raise
            if page is None or context is None:
                raise RuntimeError("Failed to create browser context/page")

            # Set viewport size for screenshot
            await page.set_viewport_size(
                {"width": screenshot_input.width, "height": screenshot_input.height}
            )

            start_time = time.perf_counter()

            try:
                logger.debug(
                    f"Created new {screenshot_input.browser_type} page for screenshot"
                )
                if screenshot_input.headers:
                    await page.set_extra_http_headers(screenshot_input.headers)

                logger.debug(
                    f"Navigating to URL for screenshot: {screenshot_input.url}"
                )
                response = await page.goto(
                    str(screenshot_input.url),
                    timeout=screenshot_input.timeout,
                    wait_until=screenshot_input.wait_until,
                )
                assert response

                logger.debug(
                    f"Page loaded, waiting for screenshot: {screenshot_input.url}"
                )
                await asyncio.sleep(2)

                # Take screenshot
                screenshot_options = {}
                if screenshot_input.full_page:
                    screenshot_options["full_page"] = True

                screenshot_bytes = await page.screenshot(**screenshot_options)
                logger.debug(f"Screenshot taken successfully: {screenshot_input.url}")

                # Encode screenshot to base64 for JSON serialization
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

                response_headers = json.dumps(response.headers)
                request_headers = json.dumps(response.request.headers)

                result = ScreenshotResponse(
                    screenshot=screenshot_base64,
                    page_status_code=response.status,
                    page_error=get_error(response.status),
                )
                # 记录页面状态码
                browser_page_status_codes_total.labels(
                    browser_type=browser_type,
                    operation=operation,
                    page_status_code=response.status,
                ).inc()
            except PWTimeoutError as e:
                # 记录超时错误
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
                        screenshot_bytes = await page.screenshot(**screenshot_options)
                        screenshot_base64 = base64.b64encode(screenshot_bytes).decode(
                            "utf-8"
                        )
                        result = ScreenshotResponse(
                            screenshot=screenshot_base64,
                            page_status_code=600,
                            page_error=f"page load timeout, {e}",
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error occurred while force taking screenshot: {e}, {screenshot_input.url}"
                        )
                        result = ScreenshotResponse(
                            screenshot="",
                            page_status_code=601,
                            page_error=f"page load failed while force taking screenshot, {e}",
                        )
                else:
                    result = ScreenshotResponse(
                        screenshot="",
                        page_status_code=601,
                        page_error=f"page load timeout, {e}",
                    )

            except Exception as e:
                logger.exception(e)
                logger.error(
                    f"Error occurred while loading page for screenshot: {e}, {screenshot_input.url}"
                )
                # 记录浏览器错误
                errors_total.labels(error_type="browser_error").inc()
                result = ScreenshotResponse(
                    screenshot="",
                    page_status_code=602,
                    page_error=f"page load failed, {e}",
                )
            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()

            end_time = time.perf_counter()
            response_time = end_time - start_time

    except Exception as e:
        logger.error(f"Error processing screenshot request: {str(e)}")
        # 记录其他错误
        errors_total.labels(error_type="other").inc()
        result = ScreenshotResponse(
            screenshot="", page_status_code=603, page_error=f"request failed, {e}"
        )

    finally:
        # 计算操作持续时间
        operation_duration = time.perf_counter() - operation_start_time

        # 记录浏览器操作指标
        browser_operations_total.labels(
            browser_type=browser_type, operation=operation
        ).inc()
        browser_operation_duration_seconds.labels(
            browser_type=browser_type, operation=operation
        ).observe(operation_duration)

        # 记录操作状态
        status_code_int = (
            int(result.page_status_code)
            if isinstance(result.page_status_code, (int, str))
            and str(result.page_status_code).isdigit()
            else 0
        )
        if status_code_int >= 200 and status_code_int < 400:
            status = "success"
        else:
            status = "failure"
        browser_operations_status_total.labels(
            browser_type=browser_type, operation=operation, status=status
        ).inc()

        # 记录页面状态码（如果还没有记录）
        if status_code_int > 0:
            browser_page_status_codes_total.labels(
                browser_type=browser_type,
                operation=operation,
                page_status_code=str(result.page_status_code),
            ).inc()

        # 减少处理中请求数
        processing_requests.dec()

        # Note: Screenshot requests don't use cache, but we still log the request history
        await RequestHistoryModel.create_request_history(
            url=screenshot_input.url,
            browser_type=screenshot_input.browser_type,
            status_code=result.page_status_code,
            response_time=response_time,
            response_headers=response_headers,
            response_body=response_body,
            request_headers=request_headers,
            request_body=request_body,
            session=session,
        )

    return result
