#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:17:56
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""

import asyncio
import time
from datetime import datetime
from typing import Literal

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PWTimeoutError,
    ProxySettings,
)
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from loguru import logger

from get_error import get_error
from main import cleanup_browsers, create_context
from base_proxy import ProxyManager
from models.request_history_model import RequestHistoryModel
from schemas.service_schema import (
    CleanHtmlInput,
    CleanHtmlResponse,
    HtmlResponse,
    UrlInput,
)
from config import browser_context_manager
from utils import clean_html_utils
from apis.deps import SessionDep

service_router = APIRouter()


max_concurrent_requests = 10
request_semaphore = asyncio.Semaphore(max_concurrent_requests)


async def ensure_browsers(browser_type: Literal["chrome", "firefox"]):

    if not browser_context_manager.chrome_browser and browser_type == "chrome":
        logger.info("Initializing chrome browser")
        playwright = await async_playwright().start()
        browser_context_manager.chrome_browser = await playwright.chromium.launch(
            headless=True
        )
        logger.info("Chrome browser initialized successfully")
        if (
            browser_context_manager.cleanup_task is None
            or browser_context_manager.cleanup_task.done()
        ):
            logger.info("Starting cleanup task for chrome browser")
            browser_context_manager.cleanup_task = asyncio.create_task(
                cleanup_browsers()
            )
    elif not browser_context_manager.firefox_browser and browser_type == "firefox":
        logger.info("Initializing firefox browser")
        playwright = await async_playwright().start()
        browser_context_manager.firefox_browser = await playwright.firefox.launch(
            headless=True
        )
        logger.info("Firefox browser initialized successfully")
        if (
            browser_context_manager.cleanup_task is None
            or browser_context_manager.cleanup_task.done()
        ):
            logger.info("Starting cleanup task")
            browser_context_manager.cleanup_task = asyncio.create_task(
                cleanup_browsers()
            )


@service_router.post("/html")
async def get_html(url_input: UrlInput, session: SessionDep):
    """
    Get HTML content from a URL.

    ATT:
        - switch proxy will reduce context performance

    Args:
        url_input: The URL to get HTML content from

    Returns:
        HTML content from the URL
    """

    status_code = 0
    response_time = 0
    response_headers = ""
    response_body = ""
    request_headers = ""
    request_body = ""
    result = None

    try:
        waiting_requests = get_waiting_requests()
        if waiting_requests > 0:
            logger.info(
                f"Request for {url_input.url} is waiting. Current waiting requests: {waiting_requests}"
            )

        proxy = await ProxyManager().get_proxy()
        proxy_item = ProxySettings(server=proxy) if proxy else None

        async with request_semaphore:
            logger.info(
                f"Received request for URL: {url_input.url} using browser: {url_input.browser_type}"
            )
            await ensure_browsers(url_input.browser_type)
            browser_context_manager.last_request_time = datetime.now()
            browser = (
                browser_context_manager.chrome_browser
                if url_input.browser_type == "chrome"
                else browser_context_manager.firefox_browser
            )

            context = await create_context(browser, proxy_item)
            page: Page = await context.new_page()

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
                await asyncio.sleep(2)

                html = await page.content()
                logger.debug(f"Page closed successfully: {url_input.url}")
                result = HtmlResponse(
                    html=html,
                    page_status_code=response.status,
                    page_error=get_error(response.status),
                )
            except PWTimeoutError as e:
                logger.warning(f"Page load timeout: {e}, {url_input.url}")
                if url_input.is_force_get_content:
                    try:
                        if (html_content := await page.content()) and len(
                            html_content
                        ) > 5000:
                            result = HtmlResponse(
                                html=html_content,
                                page_status_code=600,
                                page_error=f"page load timeout, {e}",
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
        result = HtmlResponse(
            html="", page_status_code=603, page_error=f"request failed, {e}"
        )

    finally:
        await RequestHistoryModel.create_request_history(
            url=url_input.url,
            status_code=status_code,
            response_time=response_time,
            response_headers=response_headers,
            response_body=response_body,
            request_headers=request_headers,
            request_body=request_body,
            session=session,
        )

    return result


@service_router.post("/clean_html", response_model=CleanHtmlResponse)
async def clean_html(clean_html_input: CleanHtmlInput):
    """
    Clean HTML content to reduce token count while preserving important information.
    This function removes unnecessary tags and content to make the HTML suitable for LLM input.

    Args:
        html: The original HTML content to clean

    Returns:
        Cleaned HTML with reduced token count but preserved important information
    """

    if not clean_html_input.html:
        return clean_html_input.html
    clean_text = clean_html_utils(clean_html_input.html, clean_html_input.parser)
    return CleanHtmlResponse(html=clean_text)


@service_router.get("/health/liveness")
def liveness_probe():
    return JSONResponse(content={"status": "ok"}, status_code=200)


@service_router.get("/health/readiness")
async def readiness_probe(browser_type: Literal["chrome", "firefox"]):
    if browser_type == "chrome":
        if browser_context_manager.chrome_browser:
            return JSONResponse(content={"status": "ok"}, status_code=200)
        else:
            return JSONResponse(
                content={"status": "Chrome Service Unavailable"}, status_code=503
            )
    else:
        if browser_context_manager.firefox_browser:
            return JSONResponse(content={"status": "ok"}, status_code=200)
        else:
            return JSONResponse(
                content={"status": "Firefox Service Unavailable"}, status_code=503
            )


def get_waiting_requests() -> int:
    if request_semaphore._waiters:
        return len(request_semaphore._waiters)
    else:
        return 0
