#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:01:55
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Firefox Browser Implementation
All Rights Reserved.
"""

from typing import Optional
from patchright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    ProxySettings,
)

from .base_browser import BaseBrowser


class FirefoxBrowser(BaseBrowser):
    """Firefox Browser Implementation"""

    def __init__(self):
        super().__init__("Firefox")

    async def initialize(self, **kwargs) -> Browser:
        """Initialize Firefox browser

        Args:
            headless: Run browser in headless mode (default: True)
            args: Additional browser arguments to pass
            firefox_user_prefs: Firefox user preferences (dict)
            slow_mo: Slow down operations by specified milliseconds
        """
        # Save playwright instance to ensure proper cleanup
        self.playwright = await async_playwright().start()

        # Default Firefox user preferences (equivalent to Chromium args where applicable)
        default_prefs = {
            "intl.accept_languages": "zh-CN,zh",  # Equivalent to --lang=zh-CN
            "layout.css.devPixelsPerPx": "1.0",  # Equivalent to --force-device-scale-factor=1
            "media.navigator.streams.fake": True,  # Equivalent to --use-fake-device-for-media-stream
            "media.navigator.permission.disabled": True,  # Auto-allow media permissions
        }

        # Merge default prefs with user-provided prefs
        user_prefs = kwargs.get("firefox_user_prefs", {})
        merged_prefs = {**default_prefs, **user_prefs}

        # Default browser arguments for WAF bypass
        default_args = kwargs.get("args", [])
        if not default_args:
            default_args = []

        browser = await self.playwright.firefox.launch(
            headless=kwargs.get("headless", True),
            args=default_args,
            firefox_user_prefs=merged_prefs,
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
        extra_http_headers: Optional[dict] = None,
        enable_waf_bypass: bool = True,
    ) -> BrowserContext:
        """Create Firefox browser context

        Args:
            proxy: Proxy settings for the context
            user_agent: Custom User-Agent string
            viewport: Viewport size, e.g. {"width": 1920, "height": 1080}
            locale: Locale for the context, e.g. "zh-CN"
            timezone_id: Timezone ID, e.g. "Asia/Shanghai"
            geolocation: Geolocation, e.g. {"latitude": 31.2, "longitude": 121.5}
            extra_http_headers: Additional HTTP headers
            enable_waf_bypass: Enable WAF bypass features (default: True)
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized")

        # Get default WAF-optimized settings from base class
        default_settings = self.get_default_waf_settings()
        default_headers = self.get_default_waf_headers()

        # Default values optimized for WAF bypass
        default_user_agent = (
            user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        default_viewport = viewport or default_settings["viewport"]
        default_locale = locale or default_settings["locale"]
        default_timezone = timezone_id or default_settings["timezone_id"]
        default_geolocation = geolocation or default_settings["geolocation"]

        # Merge user-provided headers with defaults
        if extra_http_headers:
            merged_headers = {**default_headers, **extra_http_headers}
        else:
            merged_headers = default_headers

        context = await self.browser.new_context(
            ignore_https_errors=True,
            proxy=proxy,
            user_agent=default_user_agent,
            viewport=default_viewport,
            locale=default_locale,
            timezone_id=default_timezone,
            geolocation=default_geolocation,
            permissions=["geolocation"],
            extra_http_headers=merged_headers,
        )

        # Add anti-detection scripts for WAF bypass
        if enable_waf_bypass:
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Firefox specific properties
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en-US', 'en']
                });
                
                // Override permissions API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)

        # Block media files to improve performance (optional, can be disabled if needed)
        await context.route(
            "**/*.{png,jpg,jpeg,gif,svg,mp3,mp4,avi,flac,ogg,wav,webm}",
            handler=lambda route, request: route.abort(),
        )

        return context

    async def create_page(self, context: BrowserContext) -> Page:
        """Create Firefox page"""
        return await context.new_page()
