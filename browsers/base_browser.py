#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:01:55
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Browser Abstract Base Class
All Rights Reserved.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from patchright.async_api import Browser, BrowserContext, Page, ProxySettings
from loguru import logger


class BaseBrowser(ABC):
    """Browser Abstract Base Class"""

    def __init__(self, name: str):
        self.name = name
        self.browser: Optional[Browser] = None
        self.playwright: Optional[Any] = None  # Playwright instance
        self._is_initialized = False

    @staticmethod
    def get_default_waf_headers() -> Dict[str, str]:
        """Get default HTTP headers optimized for WAF bypass
        
        Returns:
            Dictionary of default HTTP headers
        """
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    @staticmethod
    def get_default_waf_settings() -> Dict:
        """Get default browser settings optimized for WAF bypass
        
        Returns:
            Dictionary with default viewport, locale, timezone, and geolocation
        """
        return {
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "geolocation": {"latitude": 39.9, "longitude": 116.4},
        }

    @abstractmethod
    async def initialize(self, **kwargs) -> Browser:
        """Initialize browser instance"""
        pass

    @abstractmethod
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
        """Create browser context

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
        pass

    @abstractmethod
    async def create_page(self, context: BrowserContext) -> Page:
        """Create page"""
        pass

    async def close(self):
        """Close browser and playwright instance"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        self._is_initialized = False
        logger.info(f"{self.name} browser closed")

    @property
    def is_initialized(self) -> bool:
        """Check if browser is initialized"""
        return self._is_initialized and self.browser is not None

    async def ensure_initialized(self, **kwargs) -> Browser:
        """Ensure browser is initialized"""
        if not self.is_initialized:
            self.browser = await self.initialize(**kwargs)
            self._is_initialized = True
            logger.info(f"{self.name} browser initialized")
        return self.browser
