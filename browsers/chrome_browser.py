#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:01:55
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Chrome Browser Implementation
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


class ChromeBrowser(BaseBrowser):
    """Chrome Browser Implementation"""

    def __init__(self):
        super().__init__("Chrome")

    async def initialize(self, **kwargs) -> Browser:
        """Initialize Chrome browser

         Args:
             headless: Run browser in headless mode (default: True)
             args: Additional browser arguments to pass
             devtools: Open DevTools automatically (Chromium only, default: False)
             chromium_sandbox: Enable Chromium sandbox (default: False)
             slow_mo: Slow down operations by specified milliseconds

        args=[
             '--timezone=Asia',
             # f'--proxy-server={get_proxy()}',
             '--fpseed=12lfisffwfaTYa',
             '--chrome-version=130.0.7151.70',
             '--noimage',
             '--nocrash',
             '--lang=zh-CN',
             '--accept-lang=zh-CN',
             '-cpucores=6',
             '--platformversion=15.4.1',
             '--custom-screen=1792x1120',
             '--force-device-scale-factor=1',
             '--custom-geolocation=110,220',
             '--use-fake-device-for-media-stream',
             '--custom-brand="Microsoft Edge"',
             '--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"',
             '--close-portscan',
             '--iconumber=1',
         ],
        """
        playwright = await async_playwright().start()

        # Valid Chromium-specific arguments
        default_args = [
            "--lang=zh-CN",
            "--force-device-scale-factor=1",
            "--use-fake-device-for-media-stream",
        ]

        # Merge default args with user-provided args
        user_args = kwargs.get("args", [])
        merged_args = default_args + user_args

        browser = await playwright.chromium.launch(
            headless=kwargs.get("headless", True),
            args=merged_args,
            devtools=kwargs.get("devtools", False),
            chromium_sandbox=kwargs.get("chromium_sandbox", False),
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
        """Create Chrome browser context

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
        """Create Chrome page"""
        return await context.new_page()
