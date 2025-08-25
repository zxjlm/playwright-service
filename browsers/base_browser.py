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
from playwright.async_api import Browser, BrowserContext, Page, ProxySettings
from loguru import logger


class BaseBrowser(ABC):
    """Browser Abstract Base Class"""
    
    def __init__(self, name: str):
        self.name = name
        self.browser: Optional[Browser] = None
        self._is_initialized = False
    
    @abstractmethod
    async def initialize(self, **kwargs) -> Browser:
        """Initialize browser instance"""
        pass
    
    @abstractmethod
    async def create_context(self, proxy: Optional[ProxySettings] = None) -> BrowserContext:
        """Create browser context"""
        pass
    
    @abstractmethod
    async def create_page(self, context: BrowserContext) -> Page:
        """Create page"""
        pass
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
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
