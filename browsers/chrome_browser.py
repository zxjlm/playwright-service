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
from patchright.async_api import (
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
             headless: Run browser in headless mode (default: False for better WAF bypass)
             args: Additional browser arguments to pass
             devtools: Open DevTools automatically (Chromium only, default: False)
             chromium_sandbox: Enable Chromium sandbox (default: False)
             slow_mo: Slow down operations by specified milliseconds
        """
        playwright = await async_playwright().start()

        # Default Chromium arguments optimized for WAF bypass
        # Key: --disable-blink-features=AutomationControlled is critical for bypassing navigator.webdriver detection
        default_args = [
            "--disable-blink-features=AutomationControlled",  # Critical for WAF bypass
            "--lang=zh-CN",
            "--accept-lang=zh-CN",
            "--force-device-scale-factor=1",
            "--use-fake-device-for-media-stream",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ]

        # Merge default args with user-provided args
        user_args = kwargs.get("args", [])
        merged_args = default_args + user_args

        browser = await playwright.chromium.launch(
            headless=kwargs.get("headless", False),  # Default to False for better WAF bypass
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
        extra_http_headers: Optional[dict] = None,
        enable_waf_bypass: bool = True,
    ) -> BrowserContext:
        """Create Chrome browser context

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

        # Get default WAF-optimized settings
        default_settings = self.get_default_waf_settings()
        default_headers = self.get_default_waf_headers()

        # Default values optimized for WAF bypass
        default_user_agent = (
            user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
                // Hide webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override chrome object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Override languages
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
                
                // Override webdriver property (additional protection)
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                
                // Add realistic browser features
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8
                });
                
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
                
                // Override getBattery if available
                if (navigator.getBattery) {
                    navigator.getBattery = () => Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 1
                    });
                }
            """)

        # Block media files to improve performance (optional, can be disabled if needed)
        await context.route(
            "**/*.{png,jpg,jpeg,gif,svg,mp3,mp4,avi,flac,ogg,wav,webm}",
            handler=lambda route, request: route.abort(),
        )

        return context

    async def create_page(self, context: BrowserContext) -> Page:
        """Create Chrome page"""
        return await context.new_page()
