#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for service_router
"""

import pytest
import base64
from unittest.mock import AsyncMock, MagicMock, patch

from schemas.service_schema import (
    HtmlResponse,
    ScreenshotResponse,
)
from base_proxy import ProxyManager


class TestServiceRouter:
    """Test class for service_router"""

    def test_get_html_success(
        self,
        client,
        mock_session,
        mock_proxy_manager,
        mock_browser_manager,
        mock_browser,
        sample_url_input,
    ):
        """Test successful HTML content retrieval"""
        with (
            patch("apis.service_router.browser_manager", mock_browser_manager),
            patch("apis.utils.ProxyManager", return_value=mock_proxy_manager),
            patch("apis.service_router.get_html_base") as mock_get_html,
        ):

            # Mock successful response
            mock_response = HtmlResponse(
                html="<html><body>Test Content</body></html>",
                page_status_code=200,
                page_error="",
            )
            mock_get_html.return_value = mock_response

            response = client.post("/service/html", json=sample_url_input)

            assert response.status_code == 200
            data = response.json()
            assert data["html"] == "<html><body>Test Content</body></html>"
            assert data["page_status_code"] == 200
            assert data["page_error"] == ""

    def test_get_html_with_proxy(self, client, mock_session, sample_url_input):
        """Test HTML retrieval with proxy"""
        with (
            patch("apis.service_router.browser_manager") as mock_bm,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.service_router.get_html_base") as mock_get_html,
        ):

            # Mock proxy manager
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(
                return_value="http://127.0.0.1:8080"
            )
            mock_pm_class.return_value = mock_proxy_manager

            # Mock browser manager
            mock_browser = AsyncMock()
            mock_bm.get_browser = AsyncMock(return_value=mock_browser)

            # Mock successful response
            mock_response = HtmlResponse(
                html="<html><body>Proxy Content</body></html>",
                page_status_code=200,
                page_error="",
            )
            mock_get_html.return_value = mock_response

            response = client.post("/service/html", json=sample_url_input)

            assert response.status_code == 200
            data = response.json()
            assert "Proxy Content" in data["html"]

    def test_clean_html_success(self, client, sample_clean_html_input):
        """Test HTML cleaning functionality"""
        with patch("apis.service_router.clean_html_utils") as mock_clean:
            mock_clean.return_value = "<html><body>Cleaned Content</body></html>"

            response = client.post("/service/clean_html", json=sample_clean_html_input)

            assert response.status_code == 200
            data = response.json()
            assert data["html"] == "<html><body>Cleaned Content</body></html>"

    def test_clean_html_empty_input(self, client):
        """Test empty HTML input"""
        empty_input = {"html": "", "parser": "html.parser"}

        response = client.post("/service/clean_html", json=empty_input)

        assert response.status_code == 200
        data = response.json()
        assert data["html"] == ""

    def test_get_browser_info_available(self, client):
        """Test getting available browser information"""
        with patch("apis.service_router.browser_manager") as mock_bm:
            mock_bm.is_browser_available.return_value = True

            response = client.get("/service/browsers/chrome/info")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "chrome Service Available"

    def test_get_browser_info_unavailable(self, client):
        """Test getting unavailable browser information"""
        with patch("apis.service_router.browser_manager") as mock_bm:
            mock_bm.is_browser_available.return_value = False

            response = client.get("/service/browsers/chrome/info")

            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "chrome Service Unavailable"

    def test_get_supported_browsers(self, client):
        """Test getting supported browser list"""
        with patch("apis.service_router.browser_manager") as mock_bm:
            mock_bm.get_supported_browsers.return_value = [
                "chrome",
                "firefox",
                "webkit",
            ]

            response = client.get("/service/browsers/supported")

            assert response.status_code == 200
            data = response.json()
            assert data["browsers"] == ["chrome", "firefox", "webkit"]

    def test_liveness_probe(self, client):
        """Test liveness probe"""
        response = client.get("/service/health/liveness")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_readiness_probe_available(self, client):
        """Test readiness probe - browser available"""
        with patch("apis.service_router.browser_manager") as mock_bm:
            mock_bm.is_browser_available.return_value = True

            response = client.get("/service/health/readiness?browser_type=chrome")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    def test_readiness_probe_unavailable(self, client):
        """Test readiness probe - browser unavailable"""
        with patch("apis.service_router.browser_manager") as mock_bm:
            mock_bm.is_browser_available.return_value = False

            response = client.get("/service/health/readiness?browser_type=chrome")

            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "chrome Service Unavailable"

    def test_get_screenshot_success(
        self, client, mock_session, sample_screenshot_input
    ):
        """Test successful screenshot retrieval"""
        with (
            patch("apis.service_router.browser_manager") as mock_bm,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.service_router.get_html_screenshot") as mock_screenshot,
        ):

            # Mock proxy manager
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(
                return_value="http://127.0.0.1:8080"
            )
            mock_pm_class.return_value = mock_proxy_manager

            # Mock successful response
            mock_response = ScreenshotResponse(
                screenshot=base64.b64encode(b"fake_screenshot_data").decode("utf-8"),
                page_status_code=200,
                page_error="",
            )
            mock_screenshot.return_value = mock_response

            response = client.post("/service/screenshot", json=sample_screenshot_input)

            assert response.status_code == 200
            data = response.json()
            assert data["screenshot"] == base64.b64encode(
                b"fake_screenshot_data"
            ).decode("utf-8")
            assert data["page_status_code"] == 200
            assert data["page_error"] == ""

    def test_invalid_browser_type(self, client, sample_url_input):
        """Test invalid browser type"""
        invalid_input = sample_url_input.copy()
        invalid_input["browser_type"] = "invalid_browser"

        response = client.post("/service/html", json=invalid_input)

        # 应该返回422验证错误
        assert response.status_code == 422

    def test_invalid_url(self, client, sample_url_input):
        """Test invalid URL"""
        invalid_input = sample_url_input.copy()
        invalid_input["url"] = "not-a-valid-url"

        response = client.post("/service/html", json=invalid_input)

        # Should return 422 validation error
        assert response.status_code == 422

    def test_timeout_validation(self, client, sample_url_input):
        """Test timeout validation"""
        # Test timeout too short
        invalid_input = sample_url_input.copy()
        invalid_input["timeout"] = 500  # Less than minimum 1000

        response = client.post("/service/html", json=invalid_input)
        assert response.status_code == 422

        # Test timeout too long
        invalid_input["timeout"] = 200000  # Greater than maximum 100000

        response = client.post("/service/html", json=invalid_input)
        assert response.status_code == 422


class TestProxyManagerMock:
    """ProxyManager mock tests"""

    @pytest.mark.asyncio
    async def test_proxy_manager_get_proxy_dynamic(self):
        """Test dynamic proxy retrieval"""
        with patch("base_proxy.service_config") as mock_config:
            mock_config.proxy_type = "dynamic"
            mock_config.proxy_api_url = "http://test-proxy-api.com"

            # Mock the actual proxy API call
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = "http://127.0.0.1:8080"
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client_class.return_value.__aenter__.return_value = mock_client

                proxy_manager = ProxyManager()
                proxy = await proxy_manager.get_proxy()

                assert proxy == "http://127.0.0.1:8080"

    @pytest.mark.asyncio
    async def test_proxy_manager_get_proxy_static(self):
        """Test static proxy retrieval"""
        with patch("base_proxy.service_config") as mock_config:
            mock_config.proxy_type = "static"
            mock_config.static_proxy = "http://127.0.0.1:3128"

            proxy_manager = ProxyManager()
            proxy = await proxy_manager.get_proxy()

            assert proxy == "http://127.0.0.1:3128"

    @pytest.mark.asyncio
    async def test_proxy_manager_get_proxy_none(self):
        """Test no proxy mode"""
        with patch("base_proxy.service_config") as mock_config:
            mock_config.proxy_type = "none"

            proxy_manager = ProxyManager()
            proxy = await proxy_manager.get_proxy()

            assert proxy is None

    @pytest.mark.asyncio
    async def test_proxy_manager_check_proxy_success(self):
        """Test proxy check success"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            proxy_manager = ProxyManager()
            result = await proxy_manager.check_proxy("http://127.0.0.1:8080")

            assert result is True

    @pytest.mark.asyncio
    async def test_proxy_manager_check_proxy_failure(self):
        """Test proxy check failure"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            proxy_manager = ProxyManager()
            result = await proxy_manager.check_proxy("http://127.0.0.1:8080")

            assert result is False

    @pytest.mark.asyncio
    async def test_proxy_manager_check_proxy_exception(self):
        """Test proxy check exception"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.head = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client_class.return_value.__aenter__.return_value = mock_client

            proxy_manager = ProxyManager()
            result = await proxy_manager.check_proxy("http://127.0.0.1:8080")

            assert result is False


class TestIntegrationComparison:
    """Integration tests - actual request comparison"""

    def test_html_content_comparison(self, client, sample_url_input):
        """Test HTML content comparison functionality"""
        with (
            patch("apis.service_router.browser_manager") as mock_bm,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.service_router.get_html_base") as mock_get_html,
        ):

            # Mock proxy manager
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(
                return_value="http://127.0.0.1:8080"
            )
            mock_pm_class.return_value = mock_proxy_manager

            # Mock browser manager
            mock_browser = AsyncMock()
            mock_bm.get_browser = AsyncMock(return_value=mock_browser)

            # Mock different response content
            mock_response_with_proxy = HtmlResponse(
                html="<html><body>Content via Proxy</body></html>",
                page_status_code=200,
                page_error="",
            )

            mock_response_without_proxy = HtmlResponse(
                html="<html><body>Content without Proxy</body></html>",
                page_status_code=200,
                page_error="",
            )

            # First request (with proxy)
            mock_get_html.return_value = mock_response_with_proxy
            response1 = client.post("/service/html", json=sample_url_input)
            assert response1.status_code == 200
            data1 = response1.json()
            assert "Proxy" in data1["html"]

            # Second request (without proxy)
            mock_proxy_manager.get_proxy = AsyncMock(return_value=None)
            mock_get_html.return_value = mock_response_without_proxy
            response2 = client.post("/service/html", json=sample_url_input)
            assert response2.status_code == 200
            data2 = response2.json()
            assert "without Proxy" in data2["html"]

            # Verify content is indeed different
            assert data1["html"] != data2["html"]

    def test_screenshot_comparison(self, client, sample_screenshot_input):
        """Test screenshot comparison functionality"""
        with (
            patch("apis.service_router.browser_manager") as mock_bm,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.service_router.get_html_screenshot") as mock_screenshot,
        ):

            # Mock proxy manager
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(
                return_value="http://127.0.0.1:8080"
            )
            mock_pm_class.return_value = mock_proxy_manager

            # Mock browser manager
            mock_browser = AsyncMock()
            mock_bm.get_browser = AsyncMock(return_value=mock_browser)

            # Mock different screenshot data
            screenshot_data_1 = base64.b64encode(b"screenshot_data_1").decode("utf-8")
            screenshot_data_2 = base64.b64encode(b"screenshot_data_2").decode("utf-8")

            mock_response_1 = ScreenshotResponse(
                screenshot=screenshot_data_1, page_status_code=200, page_error=""
            )

            mock_response_2 = ScreenshotResponse(
                screenshot=screenshot_data_2, page_status_code=200, page_error=""
            )

            # First screenshot
            mock_screenshot.return_value = mock_response_1
            response1 = client.post("/service/screenshot", json=sample_screenshot_input)
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["screenshot"] == screenshot_data_1

            # Second screenshot
            mock_screenshot.return_value = mock_response_2
            response2 = client.post("/service/screenshot", json=sample_screenshot_input)
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["screenshot"] == screenshot_data_2

            # Verify screenshot data is indeed different
            assert data1["screenshot"] != data2["screenshot"]

    def test_error_handling_comparison(self, client, sample_url_input):
        """Test error handling comparison"""
        with (
            patch("apis.service_router.browser_manager") as mock_bm,
            patch("apis.utils.ProxyManager") as mock_pm_class,
            patch("apis.service_router.get_html_base") as mock_get_html,
        ):

            # Mock proxy manager
            mock_proxy_manager = MagicMock()
            mock_proxy_manager.get_proxy = AsyncMock(
                return_value="http://127.0.0.1:8080"
            )
            mock_pm_class.return_value = mock_proxy_manager

            # Mock browser manager
            mock_browser = AsyncMock()
            mock_bm.get_browser = AsyncMock(return_value=mock_browser)

            # Mock timeout error
            mock_timeout_response = HtmlResponse(
                html="",
                page_status_code=601,
                page_error="page load timeout, TimeoutError",
            )

            # Mock network error
            mock_network_error_response = HtmlResponse(
                html="",
                page_status_code=602,
                page_error="page load failed, NetworkError",
            )

            # Test timeout error
            mock_get_html.return_value = mock_timeout_response
            response1 = client.post("/service/html", json=sample_url_input)
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["page_status_code"] == 601
            assert "timeout" in data1["page_error"]

            # Test network error
            mock_get_html.return_value = mock_network_error_response
            response2 = client.post("/service/html", json=sample_url_input)
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["page_status_code"] == 602
            assert "failed" in data2["page_error"]

            # Verify error types are different
            assert data1["page_status_code"] != data2["page_status_code"]
            assert data1["page_error"] != data2["page_error"]
