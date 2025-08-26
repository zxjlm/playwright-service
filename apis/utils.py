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
import json
import time
from loguru import logger
from playwright.async_api import (
    Page,
    TimeoutError as PWTimeoutError,
    ProxySettings,
)
from base_proxy import ProxyManager
from get_error import get_error
from schemas.service_schema import HtmlResponse
from schemas.service_schema import UrlInput
from models.request_history_model import RequestHistoryModel
from config import request_semaphore
from browsers import browser_manager


def get_waiting_requests() -> int:
    if request_semaphore._waiters:
        return len(request_semaphore._waiters)
    else:
        return 0


async def get_html_base(url_input: UrlInput, session) -> HtmlResponse:
    status_code = 0
    response_time = 0
    response_headers = ""
    response_body = ""
    request_headers = ""
    request_body = url_input.model_dump_json()
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

            # Use new browser manager
            browser_instance = await browser_manager.get_browser(
                url_input.browser_type, headless=True
            )
            context = await browser_instance.create_context(proxy_item)
            page: Page = await browser_instance.create_page(context)

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

                response_body = html = await page.content()
                logger.debug(f"Page closed successfully: {url_input.url}")

                response_headers = json.dumps(response.headers)
                request_headers = json.dumps(response.request.headers)

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
            browser_type=url_input.browser_type,
            status_code=status_code,
            response_time=response_time,
            response_headers=response_headers,
            response_body=response_body,
            request_headers=request_headers,
            request_body=request_body,
            session=session,
        )

    return result
