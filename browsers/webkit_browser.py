#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:01:55
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: WebKit Browser Implementation
All Rights Reserved.
"""

from typing import Optional
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    ProxySettings,
)

from .base_browser import BaseBrowser


class WebKitBrowser(BaseBrowser):
    """WebKit Browser Implementation"""

    def __init__(self):
        super().__init__("WebKit")

    async def initialize(self, **kwargs) -> Browser:
        """Initialize WebKit browser

        Args:
            headless: Run browser in headless mode (default: True)
            args: Additional browser arguments to pass
            slow_mo: Slow down operations by specified milliseconds
        """
        playwright = await async_playwright().start()
        browser = await playwright.webkit.launch(
            headless=kwargs.get("headless", True),
            args=kwargs.get("args", []),
            slow_mo=kwargs.get("slow_mo"),
        )
        return browser

    async def create_context(
        self,
        proxy: Optional[ProxySettings] = None,
        user_agent: Optional[str] = None,
        viewport: Optional[dict] = None,
        locale: Optional[str] = None,
        timezone_id: Optional[str] = None,
        geolocation: Optional[dict] = None,
    ) -> BrowserContext:
        """Create WebKit browser context

        Args:
            proxy: Proxy settings for the context
            user_agent: Custom User-Agent string
            viewport: Viewport size, e.g. {"width": 1920, "height": 1080}
            locale: Locale for the context, e.g. "zh-CN"
            timezone_id: Timezone ID, e.g. "Asia/Shanghai"
            geolocation: Geolocation, e.g. {"latitude": 31.2, "longitude": 121.5}
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized")

        context = await self.browser.new_context(
            ignore_https_errors=True,
            proxy=proxy,
            user_agent=user_agent,
            viewport=viewport,
            locale=locale,
            timezone_id=timezone_id,
            geolocation=geolocation,
        )

        # Block media files to improve performance
        await context.route(
            "**/*.{png,jpg,jpeg,gif,svg,mp3,mp4,avi,flac,ogg,wav,webm}",
            handler=lambda route, request: route.abort(),
        )

        return context

    async def create_page(self, context: BrowserContext) -> Page:
        """Create WebKit page"""
        return await context.new_page()
