#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:01:55
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Browser Manager
All Rights Reserved.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from .browser_factory import BrowserFactory
from .base_browser import BaseBrowser


class BrowserManager:
    """Browser Manager"""
    
    def __init__(self):
        self.last_request_time: Optional[datetime] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 60  # Cleanup check interval (seconds)
        self._idle_timeout = 10  # Idle timeout (minutes)
    
    async def get_browser(self, browser_type: str, **kwargs) -> BaseBrowser:
        """Get browser instance, ensure it's initialized"""
        browser = BrowserFactory.get_browser(browser_type)
        await browser.ensure_initialized(**kwargs)
        self.last_request_time = datetime.now()
        
        # Start cleanup task
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_monitor())
        
        return browser
    
    async def _cleanup_monitor(self):
        """Monitor browser idle status, auto cleanup"""
        while True:
            await asyncio.sleep(self._cleanup_interval)
            
            if (self.last_request_time and 
                datetime.now() - self.last_request_time > timedelta(minutes=self._idle_timeout)):
                logger.info(f"No requests for {self._idle_timeout} minutes, cleaning up browsers")
                await self.cleanup_all_browsers()
                break
    
    async def cleanup_all_browsers(self):
        """Clean up all browsers"""
        await BrowserFactory.close_all_browsers()
        self.last_request_time = None
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
        logger.info("All browsers cleaned up")
    
    def get_supported_browsers(self) -> list[str]:
        """Get list of supported browser types"""
        return BrowserFactory.get_supported_browsers()
    
    def is_browser_available(self, browser_type: str) -> bool:
        """Check if browser is available"""
        try:
            browser = BrowserFactory.get_browser(browser_type)
            return browser.is_initialized
        except ValueError:
            return False


# Global browser manager instance
browser_manager = BrowserManager()
