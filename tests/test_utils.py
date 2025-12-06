#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for utils module
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from playwright.async_api import TimeoutError as PWTimeoutError

from apis.utils import get_html_base, get_html_screenshot, get_waiting_requests
from schemas.service_schema import (
    UrlInput,
    ScreenshotInput,
    HtmlResponse,
    ScreenshotResponse,
)
from base_proxy import ProxyManager


class TestUtilsFunctions:
    """Test class for utils module"""

    def test_get_waiting_requests_with_waiters(self):
        """Test getting waiting request count - with waiters"""
        with patch("apis.utils.request_semaphore") as mock_semaphore:
            mock_semaphore._waiters = [MagicMock(), MagicMock(), MagicMock()]

            result = get_waiting_requests()

            assert result == 3

    def test_get_waiting_requests_without_waiters(self):
        """Test getting waiting request count - without waiters"""
        with patch("apis.utils.request_semaphore") as mock_semaphore:
            mock_semaphore._waiters = []

            result = get_waiting_requests()

            assert result == 0

    def test_get_waiting_requests_none_waiters(self):
        """Test getting waiting request count - waiters is None"""
        with patch("apis.utils.request_semaphore") as mock_semaphore:
            mock_semaphore._waiters = None

            result = get_waiting_requests()

            assert result == 0

    @pytest.mark.asyncio
    async def test_get_html_base_success(self, mock_session):
        """Test successful HTML content retrieval"""
        url_input = UrlInput(
            url="https://example.com",
            browser_type="chrome",
            timeout=10000,
            wait_until="domcontentloaded",
        )

        with (
            patch("apis.utils.request_semaphore") as mock_semaphore,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.utils.browser_manager") as mock_bm,
            patch("apis.utils.RequestHistoryModel") as mock_model,
        ):

            # Mock proxy manager
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(
                return_value="http://127.0.0.1:8080"
            )
            mock_pm_class.return_value = mock_proxy_manager

            # Mock browser
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            mock_browser.create_context = AsyncMock(return_value=mock_context)
            mock_browser.create_page = AsyncMock(return_value=mock_page)
            mock_bm.get_browser = AsyncMock(return_value=mock_browser)

            # Mock page response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.request.headers = {"user-agent": "test"}

            mock_page.goto = AsyncMock(return_value=mock_response)
            mock_page.content = AsyncMock(
                return_value="<html><body>Test Content</body></html>"
            )
            mock_page.set_extra_http_headers = AsyncMock()
            mock_page.close = AsyncMock()
            mock_context.close = AsyncMock()

            # Mock semaphore
            mock_semaphore.__aenter__ = AsyncMock()
            mock_semaphore.__aexit__ = AsyncMock()

            # Mock request history model
            mock_model.get_request_history = AsyncMock(return_value=None)
            mock_model.create_request_history = AsyncMock()

            result = await get_html_base(url_input, mock_session)

            assert isinstance(result, HtmlResponse)
            assert result.html == "<html><body>Test Content</body></html>"
            assert result.page_status_code == 200
            assert result.page_error == ""

    @pytest.mark.asyncio
    async def test_get_html_base_with_cache(self, mock_session):
        """Test HTML content retrieval with cache"""
        url_input = UrlInput(
            url="https://example.com", browser_type="chrome", use_cache=1
        )

        with patch("apis.utils.RequestHistoryModel") as mock_model:
            # Mock cache hit
            mock_cached_response = MagicMock()
            mock_cached_response.response_body = (
                "<html><body>Cached Content</body></html>"
            )
            mock_cached_response.status_code = 200

            mock_model.get_request_history = AsyncMock(
                return_value=mock_cached_response
            )

            result = await get_html_base(url_input, mock_session)

            assert isinstance(result, HtmlResponse)
            assert result.html == "<html><body>Cached Content</body></html>"
            assert result.page_status_code == 200
            assert result.cache_hit == 1

    @pytest.mark.asyncio
    async def test_get_html_base_timeout_error(self, mock_session):
        """Test page load timeout error"""
        url_input = UrlInput(
            url="https://example.com", browser_type="chrome", is_force_get_content=0
        )

        with (
            patch("apis.utils.request_semaphore") as mock_semaphore,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.utils.browser_manager") as mock_bm,
            patch("apis.utils.RequestHistoryModel") as mock_model,
        ):

            # Mock proxy manager
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(return_value=None)
            mock_pm_class.return_value = mock_proxy_manager

            # Mock browser
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            mock_browser.create_context = AsyncMock(return_value=mock_context)
            mock_browser.create_page = AsyncMock(return_value=mock_page)
            mock_bm.get_browser = AsyncMock(return_value=mock_browser)

            # Mock timeout error
            mock_page.goto = AsyncMock(side_effect=PWTimeoutError("Timeout"))
            mock_page.close = AsyncMock()
            mock_context.close = AsyncMock()

            # Mock semaphore
            mock_semaphore.__aenter__ = AsyncMock()
            mock_semaphore.__aexit__ = AsyncMock()

            # Mock request history model
            mock_model.get_request_history = AsyncMock(return_value=None)
            mock_model.create_request_history = AsyncMock()

            result = await get_html_base(url_input, mock_session)

            assert isinstance(result, HtmlResponse)
            assert result.html == ""
            assert result.page_status_code == 601
            assert "timeout" in result.page_error

    @pytest.mark.asyncio
    async def test_get_html_base_force_content_on_timeout(self, mock_session):
        """Test forced content retrieval on timeout"""
        url_input = UrlInput(
            url="https://example.com", browser_type="chrome", is_force_get_content=1
        )

        with (
            patch("apis.utils.request_semaphore") as mock_semaphore,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.utils.browser_manager") as mock_bm,
            patch("apis.utils.RequestHistoryModel") as mock_model,
        ):

            # Mock proxy manager
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(return_value=None)
            mock_pm_class.return_value = mock_proxy_manager

            # Mock browser
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            mock_browser.create_context = AsyncMock(return_value=mock_context)
            mock_browser.create_page = AsyncMock(return_value=mock_page)
            mock_bm.get_browser = AsyncMock(return_value=mock_browser)

            # Mock timeout error, but forced content retrieval succeeds
            mock_page.goto = AsyncMock(side_effect=PWTimeoutError("Timeout"))
            mock_page.content = AsyncMock(
                return_value="<html><body>" + "Force Content " * 1000 + "</body></html>"
            )
            mock_page.close = AsyncMock()
            mock_context.close = AsyncMock()

            # Mock semaphore
            mock_semaphore.__aenter__ = AsyncMock()
            mock_semaphore.__aexit__ = AsyncMock()

            # Mock request history model
            mock_model.get_request_history = AsyncMock(return_value=None)
            mock_model.create_request_history = AsyncMock()

            result = await get_html_base(url_input, mock_session)

            assert isinstance(result, HtmlResponse)
            assert len(result.html) > 5000  # Check that we got the long content
            assert result.page_status_code == 600
            assert "timeout" in result.page_error

    @pytest.mark.asyncio
    async def test_get_html_screenshot_success(self, mock_session):
        """Test successful screenshot retrieval"""
        screenshot_input = ScreenshotInput(
            url="https://example.com", browser_type="chrome", width=1920, height=1080
        )

        with (
            patch("apis.utils.request_semaphore") as mock_semaphore,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.utils.browser_manager") as mock_bm,
            patch("apis.utils.RequestHistoryModel") as mock_model,
        ):

            # Mock proxy manager
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(
                return_value="http://127.0.0.1:8080"
            )
            mock_pm_class.return_value = mock_proxy_manager

            # Mock browser
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            mock_browser.create_context = AsyncMock(return_value=mock_context)
            mock_browser.create_page = AsyncMock(return_value=mock_page)
            mock_bm.get_browser = AsyncMock(return_value=mock_browser)

            # Mock page response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.request.headers = {"user-agent": "test"}

            mock_page.goto = AsyncMock(return_value=mock_response)
            mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
            mock_page.set_extra_http_headers = AsyncMock()
            mock_page.set_viewport_size = AsyncMock()
            mock_page.close = AsyncMock()
            mock_context.close = AsyncMock()

            # Mock semaphore
            mock_semaphore.__aenter__ = AsyncMock()
            mock_semaphore.__aexit__ = AsyncMock()

            # Mock request history model
            mock_model.create_request_history = AsyncMock()

            result = await get_html_screenshot(screenshot_input, mock_session)

            assert isinstance(result, ScreenshotResponse)
            assert result.screenshot == "ZmFrZV9zY3JlZW5zaG90X2RhdGE="  # base64 encoded
            assert result.page_status_code == 200
            assert result.page_error == ""

    @pytest.mark.asyncio
    async def test_get_html_screenshot_full_page(self, mock_session):
        """Test full page screenshot"""
        screenshot_input = ScreenshotInput(
            url="https://example.com",
            browser_type="chrome",
            width=1920,
            height=1080,
            full_page=1,
        )

        with (
            patch("apis.utils.request_semaphore") as mock_semaphore,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.utils.browser_manager") as mock_bm,
            patch("apis.utils.RequestHistoryModel") as mock_model,
        ):

            # Mock proxy manager
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(return_value=None)
            mock_pm_class.return_value = mock_proxy_manager

            # Mock browser
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            mock_browser.create_context = AsyncMock(return_value=mock_context)
            mock_browser.create_page = AsyncMock(return_value=mock_page)
            mock_bm.get_browser = AsyncMock(return_value=mock_browser)

            # Mock page response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.request.headers = {"user-agent": "test"}

            mock_page.goto = AsyncMock(return_value=mock_response)
            mock_page.screenshot = AsyncMock(return_value=b"full_page_screenshot")
            mock_page.set_extra_http_headers = AsyncMock()
            mock_page.set_viewport_size = AsyncMock()
            mock_page.close = AsyncMock()
            mock_context.close = AsyncMock()

            # Mock semaphore
            mock_semaphore.__aenter__ = AsyncMock()
            mock_semaphore.__aexit__ = AsyncMock()

            # Mock request history model
            mock_model.create_request_history = AsyncMock()

            result = await get_html_screenshot(screenshot_input, mock_session)

            assert isinstance(result, ScreenshotResponse)
            assert result.screenshot == "ZnVsbF9wYWdlX3NjcmVlbnNob3Q="  # base64 encoded
            assert result.page_status_code == 200

            # Verify screenshot was called with full_page parameter
            mock_page.screenshot.assert_called_once_with(full_page=True)

    @pytest.mark.asyncio
    async def test_get_html_base_general_exception(self, mock_session):
        """Test general exception handling"""
        url_input = UrlInput(url="https://example.com", browser_type="chrome")

        with (
            patch("apis.utils.request_semaphore") as mock_semaphore,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.utils.RequestHistoryModel") as mock_model,
        ):

            # Mock proxy manager raising exception
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(
                side_effect=Exception("Proxy error")
            )
            mock_pm_class.return_value = mock_proxy_manager

            # Mock semaphore
            mock_semaphore.__aenter__ = AsyncMock()
            mock_semaphore.__aexit__ = AsyncMock()

            # Mock request history model
            mock_model.get_request_history = AsyncMock(return_value=None)
            mock_model.create_request_history = AsyncMock()

            result = await get_html_base(url_input, mock_session)

            assert isinstance(result, HtmlResponse)
            assert result.html == ""
            assert result.page_status_code == 603
            assert "request failed" in result.page_error
