#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:01:55
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Proxy management with reuse support
All Rights Reserved.
"""

from abc import ABC
import asyncio
import random
import threading
from dataclasses import dataclass, field
from typing import Optional

import httpx
from loguru import logger
import urllib3

from config import service_config


# Available proxy types
IS_ADVANCED_URLLIB3 = (
    int(urllib3.__version__.split(".")[1]) >= 26 or int(urllib3.__version__.split(".")[0]) >= 2  # type: ignore
)


# Proxy error patterns for detection
# net::ERR_TUNNEL_CONNECTION_FAILED - Chromium error when proxy tunnel fails
# NS_ERROR_PROXY_CONNECTION_REFUSED - Firefox error when proxy connection is refused
PROXY_ERROR_PATTERNS = [
    "net::ERR_TUNNEL_CONNECTION_FAILED",
    "NS_ERROR_PROXY_CONNECTION_REFUSED",
    "ERR_PROXY_CONNECTION_FAILED",
    "Proxy connection refused",
    "Could not connect to proxy",
]


def is_proxy_error(error: Exception) -> tuple[bool, str]:
    """
    Check if an exception is a proxy-related error.
    
    Args:
        error: The exception to check
        
    Returns:
        Tuple of (is_proxy_error, error_reason)
    """
    error_str = str(error)
    for pattern in PROXY_ERROR_PATTERNS:
        if pattern in error_str:
            if "TUNNEL" in pattern:
                return True, "tunnel_failed"
            elif "REFUSED" in pattern or "refused" in pattern.lower():
                return True, "connection_refused"
            else:
                return True, "other"
    return False, ""


@dataclass
class CachedProxy:
    """Represents a cached proxy with usage statistics."""
    
    server: str
    proxy_type: str
    reuse_count: int = 0
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    
    def increment_reuse(self) -> int:
        """Increment and return the reuse count."""
        self.reuse_count += 1
        return self.reuse_count


class BaseProxy(ABC):

    def __init__(self, **kwargs):
        pass

    async def get_proxy(self) -> str:
        """
        return: string like http://127.0.0.1:8080
        """
        raise NotImplementedError

    async def check_proxy(self) -> bool:
        raise NotImplementedError


class ProxyManager(BaseProxy):

    def __init__(self):
        self.proxy_url = service_config.proxy_api_url
        self.proxy_check_url = service_config.proxy_check_url
        self.proxy_type = service_config.proxy_type
        self.static_proxy = service_config.static_proxy

    async def get_proxy(self) -> None | str:
        if self.proxy_type == "dynamic":
            proxy = await self.get_api()
        elif self.proxy_type == "static":
            proxy = self.static_proxy  # type: ignore
        else:
            proxy = None
        logger.info(f"get proxy: {proxy}")
        return proxy

    async def get_api(self) -> str:
        url = self.proxy_url
        result = ""
        is_first = True
        retry_times = 0
        while True:
            logger.info(f"get proxy. url: {url}, retry_times: {retry_times}")
            retry_times += 1
            try:
                if not is_first:
                    await asyncio.sleep(2)
                is_first = False
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        url,
                        timeout=5,
                    )
                status = response.status_code
                if str(status) == "200" and response.text.strip():
                    result = response.text.strip()
                    break
                if str(status) == "400" or str(status) == "503":
                    logger.warning(response.text)
                    continue
                if not response.text.strip():
                    logger.warning("return proxy is empty")
                    continue

                if self.proxy_check_url:
                    await self.check_proxy(result)
            except Exception as e:
                logger.exception(e)
        return result

    async def check_proxy(self, proxy: str) -> bool:
        """
        Check proxy
        :param proxy:
        :return:
        """
        result = False

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        ]
        headers = {"User-Agent": random.choice(user_agents)}

        try:
            check_url = self.proxy_check_url
            async with httpx.AsyncClient(proxy=proxy) as client:
                response = await client.head(
                    url=check_url,
                    timeout=5,
                    headers=headers,
                )
            if response.status_code == 200:
                result = True
            else:
                logger.warning(f"===== > check status is {response.status_code}")
        except Exception as _e:
            logger.info(f"Check proxy failed, {_e}, regaining...")
        return result


class ProxyPool:
    """
    Singleton proxy pool that manages proxy reuse.
    
    This class caches the current proxy and tracks its usage statistics.
    When a proxy fails (detected by proxy errors), it invalidates the cache
    and fetches a new proxy.
    """
    
    _instance: Optional["ProxyPool"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "ProxyPool":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cached_proxy: Optional[CachedProxy] = None
        self._proxy_manager = ProxyManager()
        self._async_lock = asyncio.Lock()
        
        # Import metrics here to avoid circular import
        from apis.metrics import (
            proxy_reuse_count,
            proxy_current_reuse_count,
            proxy_switch_total,
        )
        self._proxy_reuse_count = proxy_reuse_count
        self._proxy_current_reuse_count = proxy_current_reuse_count
        self._proxy_switch_total = proxy_switch_total
    
    async def get_proxy(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get a proxy, reusing the cached one if available.
        
        Args:
            force_refresh: If True, force fetching a new proxy
            
        Returns:
            Proxy server string or None
        """
        async with self._async_lock:
            # If we have a cached proxy and not forcing refresh, reuse it
            if self._cached_proxy is not None and not force_refresh:
                reuse_count = self._cached_proxy.increment_reuse()
                self._proxy_current_reuse_count.set(reuse_count)
                logger.info(
                    f"Reusing cached proxy: {self._cached_proxy.server} "
                    f"(reuse count: {reuse_count})"
                )
                return self._cached_proxy.server
            
            # Need to get a new proxy
            if self._cached_proxy is not None:
                # Record the reuse count before invalidating
                self._record_proxy_reuse_stats()
            
            # Fetch new proxy
            proxy = await self._proxy_manager.get_proxy()
            
            if proxy:
                self._cached_proxy = CachedProxy(
                    server=proxy,
                    proxy_type=self._proxy_manager.proxy_type,
                    reuse_count=1,  # First use counts as 1
                )
                self._proxy_current_reuse_count.set(1)
                logger.info(f"Obtained new proxy: {proxy}")
            else:
                self._cached_proxy = None
                self._proxy_current_reuse_count.set(0)
            
            return proxy
    
    async def invalidate_proxy(self, reason: str = "unknown") -> None:
        """
        Invalidate the current cached proxy.
        
        Call this when a proxy error is detected to force fetching a new proxy.
        
        Args:
            reason: The reason for invalidation (for metrics)
        """
        async with self._async_lock:
            if self._cached_proxy is not None:
                logger.warning(
                    f"Invalidating proxy {self._cached_proxy.server} "
                    f"(reason: {reason}, reuse count: {self._cached_proxy.reuse_count})"
                )
                # Record reuse stats before invalidating
                self._record_proxy_reuse_stats()
                # Record switch reason
                self._proxy_switch_total.labels(reason=reason).inc()
                self._cached_proxy = None
                self._proxy_current_reuse_count.set(0)
    
    def _record_proxy_reuse_stats(self) -> None:
        """Record proxy reuse statistics to Prometheus."""
        if self._cached_proxy is not None and self._cached_proxy.reuse_count > 0:
            self._proxy_reuse_count.labels(
                proxy_type=self._cached_proxy.proxy_type
            ).observe(self._cached_proxy.reuse_count)
            logger.info(
                f"Proxy {self._cached_proxy.server} was reused "
                f"{self._cached_proxy.reuse_count} times"
            )
    
    @property
    def current_proxy(self) -> Optional[str]:
        """Get the current cached proxy server address."""
        if self._cached_proxy is not None:
            return self._cached_proxy.server
        return None
    
    @property
    def current_reuse_count(self) -> int:
        """Get the current proxy's reuse count."""
        if self._cached_proxy is not None:
            return self._cached_proxy.reuse_count
        return 0


# Global singleton instance
proxy_pool = ProxyPool()
