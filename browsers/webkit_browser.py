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
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, ProxySettings
from loguru import logger

from .base_browser import BaseBrowser


class WebKitBrowser(BaseBrowser):
    """WebKit Browser Implementation"""
    
    def __init__(self):
        super().__init__("WebKit")
    
    async def initialize(self, **kwargs) -> Browser:
        """Initialize WebKit browser"""
        playwright = await async_playwright().start()
        browser = await playwright.webkit.launch(
            headless=kwargs.get("headless", True),
            args=kwargs.get("args", [])
        )
        return browser
    
    async def create_context(self, proxy: Optional[ProxySettings] = None) -> BrowserContext:
        """Create WebKit browser context"""
        if not self.browser:
            raise RuntimeError("Browser not initialized")
        
        context = await self.browser.new_context(
            ignore_https_errors=True,
            proxy=proxy
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
