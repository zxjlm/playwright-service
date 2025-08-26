#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:01:55
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Browser Factory Class
All Rights Reserved.
"""

from typing import Dict, Type
from loguru import logger

from .base_browser import BaseBrowser
from .chrome_browser import ChromeBrowser
from .firefox_browser import FirefoxBrowser
from .webkit_browser import WebKitBrowser


class BrowserFactory:
    """Browser Factory Class"""
    
    _browsers: Dict[str, Type[BaseBrowser]] = {
        "chrome": ChromeBrowser,
        "firefox": FirefoxBrowser,
        "webkit": WebKitBrowser,
    }
    
    _instances: Dict[str, BaseBrowser] = {}
    
    @classmethod
    def register_browser(cls, name: str, browser_class: Type[BaseBrowser]):
        """Register new browser type"""
        cls._browsers[name] = browser_class
        logger.info(f"Registered browser: {name}")
    
    @classmethod
    def get_browser(cls, browser_type: str) -> BaseBrowser:
        """Get browser instance"""
        if browser_type not in cls._browsers:
            raise ValueError(f"Unsupported browser type: {browser_type}")
        
        if browser_type not in cls._instances:
            cls._instances[browser_type] = cls._browsers[browser_type]()
            logger.info(f"Created new {browser_type} browser instance")
        
        return cls._instances[browser_type]
    
    @classmethod
    def get_supported_browsers(cls) -> list[str]:
        """Get list of supported browser types"""
        return list(cls._browsers.keys())
    
    @classmethod
    async def close_all_browsers(cls):
        """Close all browser instances"""
        for browser_type, instance in cls._instances.items():
            await instance.close()
            logger.info(f"Closed {browser_type} browser")
        cls._instances.clear()
    
    @classmethod
    async def close_browser(cls, browser_type: str):
        """Close specified browser type"""
        if browser_type in cls._instances:
            await cls._instances[browser_type].close()
            del cls._instances[browser_type]
            logger.info(f"Closed {browser_type} browser")
