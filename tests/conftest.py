#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from base_proxy import ProxyManager
from browsers import browser_manager
from apis.service_router import service_router


# 创建测试应用
app = FastAPI()
app.include_router(service_router)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_session():
    """模拟数据库会话"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_proxy_manager():
    """模拟代理管理器"""
    manager = MagicMock(spec=ProxyManager)
    manager.get_proxy = AsyncMock(return_value="http://127.0.0.1:8080")
    manager.check_proxy = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_browser_manager():
    """模拟浏览器管理器"""
    manager = MagicMock()
    manager.get_browser = AsyncMock()
    manager.is_browser_available = MagicMock(return_value=True)
    manager.get_supported_browsers = MagicMock(
        return_value=["chrome", "firefox", "webkit"]
    )
    return manager


@pytest.fixture
def mock_browser():
    """模拟浏览器实例"""
    browser = AsyncMock()
    context = AsyncMock()
    page = AsyncMock()

    browser.create_context = AsyncMock(return_value=context)
    browser.create_page = AsyncMock(return_value=page)

    # 模拟页面响应
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.request.headers = {"user-agent": "test"}

    page.goto = AsyncMock(return_value=mock_response)
    page.content = AsyncMock(return_value="<html><body>Test Content</body></html>")
    page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
    page.set_extra_http_headers = AsyncMock()
    page.set_viewport_size = AsyncMock()
    page.close = AsyncMock()
    context.close = AsyncMock()

    return browser


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def sample_url_input():
    """示例URL输入数据"""
    return {
        "url": "https://example.com",
        "browser_type": "chrome",
        "headers": {"User-Agent": "test"},
        "timeout": 10000,
        "wait_until": "domcontentloaded",
        "is_force_get_content": 0,
        "use_cache": 0,
        "use_force_html_clean": 0,
    }


@pytest.fixture
def sample_screenshot_input():
    """示例截图输入数据"""
    return {
        "url": "https://example.com",
        "browser_type": "chrome",
        "width": 1920,
        "height": 1080,
        "full_page": 0,
        "headers": {"User-Agent": "test"},
        "timeout": 10000,
        "wait_until": "domcontentloaded",
        "is_force_get_content": 0,
    }


@pytest.fixture
def sample_clean_html_input():
    """示例清理HTML输入数据"""
    return {
        "html": "<html><head><script>alert('test')</script></head><body><div>Test Content</div></body></html>",
        "parser": "html.parser",
    }
