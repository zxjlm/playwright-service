#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for browser resource cleanup and leak prevention

This test suite verifies that playwright instances are properly cleaned up
when browser initialization fails, preventing resource leaks.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from patchright.async_api import Browser

from browsers.chrome_browser import ChromeBrowser
from browsers.firefox_browser import FirefoxBrowser
from browsers.webkit_browser import WebKitBrowser


class TestBrowserResourceCleanup:
    """Test browser resource cleanup on initialization failure"""

    @pytest.mark.asyncio
    async def test_chrome_playwright_cleanup_on_launch_failure(self):
        """Test that Chrome browser cleans up playwright instance when launch fails"""
        browser = ChromeBrowser()
        
        # Mock async_playwright to return a mock playwright instance
        mock_playwright = MagicMock()
        mock_playwright.stop = AsyncMock()
        mock_playwright.chromium = MagicMock()
        
        # Make chromium.launch raise an exception
        mock_playwright.chromium.launch = AsyncMock(
            side_effect=Exception("Browser launch failed")
        )
        
        with patch("browsers.chrome_browser.async_playwright") as mock_async_playwright:
            # Mock async_playwright().start() to return our mock
            mock_async_playwright_instance = MagicMock()
            mock_async_playwright_instance.start = AsyncMock(return_value=mock_playwright)
            mock_async_playwright.return_value = mock_async_playwright_instance
            
            # Attempt to initialize - should raise exception
            with pytest.raises(Exception, match="Browser launch failed"):
                await browser.initialize(headless=True)
            
            # Verify playwright.stop() was called during cleanup
            mock_playwright.stop.assert_called_once()
            
            # Verify playwright instance was cleared (cleanup happened)
            assert browser.playwright is None
            
            # Verify browser was not set
            assert browser.browser is None
            assert browser._is_initialized is False

    @pytest.mark.asyncio
    async def test_firefox_playwright_cleanup_on_launch_failure(self):
        """Test that Firefox browser cleans up playwright instance when launch fails"""
        browser = FirefoxBrowser()
        
        # Mock async_playwright to return a mock playwright instance
        mock_playwright = MagicMock()
        mock_playwright.stop = AsyncMock()
        mock_playwright.firefox = MagicMock()
        
        # Make firefox.launch raise an exception
        mock_playwright.firefox.launch = AsyncMock(
            side_effect=Exception("Browser launch failed")
        )
        
        with patch("browsers.firefox_browser.async_playwright") as mock_async_playwright:
            # Mock async_playwright().start() to return our mock
            mock_async_playwright_instance = MagicMock()
            mock_async_playwright_instance.start = AsyncMock(return_value=mock_playwright)
            mock_async_playwright.return_value = mock_async_playwright_instance
            
            # Attempt to initialize - should raise exception
            with pytest.raises(Exception, match="Browser launch failed"):
                await browser.initialize(headless=True)
            
            # Verify playwright.stop() was called during cleanup
            mock_playwright.stop.assert_called_once()
            
            # Verify playwright instance was cleared
            assert browser.playwright is None
            
            # Verify browser was not set
            assert browser.browser is None
            assert browser._is_initialized is False

    @pytest.mark.asyncio
    async def test_webkit_playwright_cleanup_on_launch_failure(self):
        """Test that WebKit browser cleans up playwright instance when launch fails"""
        browser = WebKitBrowser()
        
        # Mock async_playwright to return a mock playwright instance
        mock_playwright = MagicMock()
        mock_playwright.stop = AsyncMock()
        mock_playwright.webkit = MagicMock()
        
        # Make webkit.launch raise an exception
        mock_playwright.webkit.launch = AsyncMock(
            side_effect=Exception("Browser launch failed")
        )
        
        with patch("browsers.webkit_browser.async_playwright") as mock_async_playwright:
            # Mock async_playwright().start() to return our mock
            mock_async_playwright_instance = MagicMock()
            mock_async_playwright_instance.start = AsyncMock(return_value=mock_playwright)
            mock_async_playwright.return_value = mock_async_playwright_instance
            
            # Attempt to initialize - should raise exception
            with pytest.raises(Exception, match="Browser launch failed"):
                await browser.initialize(headless=True)
            
            # Verify playwright.stop() was called during cleanup
            mock_playwright.stop.assert_called_once()
            
            # Verify playwright instance was cleared
            assert browser.playwright is None
            
            # Verify browser was not set
            assert browser.browser is None
            assert browser._is_initialized is False

    @pytest.mark.asyncio
    async def test_chrome_retry_initialization_after_failure(self):
        """Test that Chrome browser can retry initialization after a failure without resource leak"""
        browser = ChromeBrowser()
        
        # First attempt: fail
        mock_playwright_fail = MagicMock()
        mock_playwright_fail.stop = AsyncMock()
        mock_playwright_fail.chromium = MagicMock()
        mock_playwright_fail.chromium.launch = AsyncMock(
            side_effect=Exception("First attempt failed")
        )
        
        # Second attempt: succeed
        mock_playwright_success = MagicMock()
        mock_playwright_success.stop = AsyncMock()
        mock_playwright_success.chromium = MagicMock()
        mock_browser = MagicMock()
        mock_browser.__class__ = Browser  # Make it pass isinstance checks
        mock_playwright_success.chromium.launch = AsyncMock(return_value=mock_browser)
        
        with patch("browsers.chrome_browser.async_playwright") as mock_async_playwright:
            # Mock async_playwright().start() to return different mocks for each call
            call_count = 0
            
            def async_playwright_factory():
                nonlocal call_count
                call_count += 1
                mock_instance = MagicMock()
                if call_count == 1:
                    mock_instance.start = AsyncMock(return_value=mock_playwright_fail)
                else:
                    mock_instance.start = AsyncMock(return_value=mock_playwright_success)
                return mock_instance
            
            mock_async_playwright.side_effect = async_playwright_factory
            
            # First attempt: should fail and clean up
            with pytest.raises(Exception, match="First attempt failed"):
                await browser.initialize(headless=True)
            
            # Verify first playwright instance was cleaned up
            mock_playwright_fail.stop.assert_called_once()
            assert browser.playwright is None
            
            # Second attempt: should succeed
            result = await browser.initialize(headless=True)
            
            # Verify second playwright instance is set and browser is returned
            assert browser.playwright is mock_playwright_success
            assert result is mock_browser
            
            # Verify second playwright.stop() was NOT called (initialization succeeded)
            mock_playwright_success.stop.assert_not_called()

    @pytest.mark.asyncio
    async def test_playwright_cleanup_exception_handling(self):
        """Test that cleanup continues even if playwright.stop() raises an exception"""
        browser = ChromeBrowser()
        
        # Mock async_playwright to return a mock playwright instance
        mock_playwright = MagicMock()
        # Make stop() raise an exception
        mock_playwright.stop = AsyncMock(side_effect=Exception("Stop failed"))
        mock_playwright.chromium = MagicMock()
        
        # Make chromium.launch raise an exception
        mock_playwright.chromium.launch = AsyncMock(
            side_effect=Exception("Browser launch failed")
        )
        
        with patch("browsers.chrome_browser.async_playwright") as mock_async_playwright:
            # Mock async_playwright().start() to return our mock
            mock_async_playwright_instance = MagicMock()
            mock_async_playwright_instance.start = AsyncMock(return_value=mock_playwright)
            mock_async_playwright.return_value = mock_async_playwright_instance
            
            # Attempt to initialize - should raise the original exception (not the cleanup exception)
            with pytest.raises(Exception, match="Browser launch failed"):
                await browser.initialize(headless=True)
            
            # Verify playwright.stop() was called (even though it failed)
            mock_playwright.stop.assert_called_once()
            
            # Verify playwright instance was still cleared despite stop() failure
            assert browser.playwright is None

    @pytest.mark.asyncio
    async def test_successful_initialization_no_cleanup(self):
        """Test that successful initialization does not trigger cleanup"""
        browser = ChromeBrowser()
        
        # Mock async_playwright to return a mock playwright instance
        mock_playwright = MagicMock()
        mock_playwright.stop = AsyncMock()
        mock_playwright.chromium = MagicMock()
        
        # Make chromium.launch succeed
        mock_browser = MagicMock()
        mock_browser.__class__ = Browser  # Make it pass isinstance checks
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        
        with patch("browsers.chrome_browser.async_playwright") as mock_async_playwright:
            # Mock async_playwright().start() to return our mock
            mock_async_playwright_instance = MagicMock()
            mock_async_playwright_instance.start = AsyncMock(return_value=mock_playwright)
            mock_async_playwright.return_value = mock_async_playwright_instance
            
            # Initialize successfully
            result = await browser.initialize(headless=True)
            
            # Verify browser was returned and playwright is set
            assert result is mock_browser
            assert browser.playwright is mock_playwright
            
            # Verify playwright.stop() was NOT called (initialization succeeded)
            mock_playwright.stop.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_cleans_up_playwright(self):
        """Test that close() method properly cleans up playwright instance"""
        browser = ChromeBrowser()
        
        # Mock async_playwright to return a mock playwright instance
        mock_playwright = MagicMock()
        mock_playwright.stop = AsyncMock()
        mock_playwright.chromium = MagicMock()
        
        # Make chromium.launch succeed
        mock_browser = MagicMock()
        mock_browser.__class__ = Browser  # Make it pass isinstance checks
        mock_browser.close = AsyncMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        
        with patch("browsers.chrome_browser.async_playwright") as mock_async_playwright:
            # Mock async_playwright().start() to return our mock
            mock_async_playwright_instance = MagicMock()
            mock_async_playwright_instance.start = AsyncMock(return_value=mock_playwright)
            mock_async_playwright.return_value = mock_async_playwright_instance
            
            # Initialize successfully and set browser manually (as ensure_initialized would do)
            browser.browser = await browser.initialize(headless=True)
            browser._is_initialized = True
            
            # Verify browser and playwright are set
            assert browser.browser is mock_browser
            assert browser.playwright is mock_playwright
            
            # Close browser
            await browser.close()
            
            # Verify both browser and playwright were closed
            mock_browser.close.assert_called_once()
            mock_playwright.stop.assert_called_once()
            
            # Verify both were cleared
            assert browser.browser is None
            assert browser.playwright is None
            assert browser._is_initialized is False

