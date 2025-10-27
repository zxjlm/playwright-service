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


from fastapi import APIRouter
from fastapi.responses import JSONResponse


from apis.utils import get_html_base, get_html_screenshot
from schemas.service_schema import (
    CleanHtmlInput,
    CleanHtmlResponse,
    HtmlResponse,
    ScreenshotInput,
    ScreenshotResponse,
    UrlInput,
)
from browsers import browser_manager
from utils import clean_html_utils
from apis.deps import SessionDep


service_router = APIRouter(prefix="/service", tags=["service"])


async def ensure_browsers(browser_type: str):
    """Ensure browser is initialized (maintain backward compatibility)"""
    await browser_manager.get_browser(browser_type, headless=True)


@service_router.post("/html", response_model=HtmlResponse)
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
    result = await get_html_base(url_input, session)
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
        return CleanHtmlResponse(html=clean_html_input.html)
    clean_text = clean_html_utils(clean_html_input.html, clean_html_input.parser)
    return CleanHtmlResponse(html=clean_text)


@service_router.get("/browsers/{browser_type}/info")
async def get_browser_info(browser_type: str):
    """Get browser information"""
    if browser_manager.is_browser_available(browser_type):
        return JSONResponse(
            content={"status": f"{browser_type} Service Available"}, status_code=200
        )
    else:
        return JSONResponse(
            content={"status": f"{browser_type} Service Unavailable"}, status_code=503
        )


@service_router.get("/browsers/supported")
async def get_supported_browsers():
    """Get list of supported browsers"""
    return JSONResponse(
        content={"browsers": browser_manager.get_supported_browsers()}, status_code=200
    )


@service_router.get("/health/liveness")
def liveness_probe():
    return JSONResponse(content={"status": "ok"}, status_code=200)


@service_router.get("/health/readiness")
async def readiness_probe(browser_type: str):
    """Health check"""
    if browser_manager.is_browser_available(browser_type):
        return JSONResponse(content={"status": "ok"}, status_code=200)
    else:
        return JSONResponse(
            content={"status": f"{browser_type} Service Unavailable"}, status_code=503
        )


@service_router.post("/screenshot", response_model=ScreenshotResponse)
async def get_screenshot(screenshot_input: ScreenshotInput, session: SessionDep):
    """Get screenshot of a URL"""

    result = await get_html_screenshot(screenshot_input, session)
    return result
