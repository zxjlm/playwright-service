#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:01:55
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""

from abc import ABC
import asyncio
import random

import httpx
from loguru import logger
import urllib3

from config import service_config


# Available proxy types
IS_ADVANCED_URLLIB3 = (
    int(urllib3.__version__.split(".")[1]) >= 26 or int(urllib3.__version__.split(".")[0]) >= 2  # type: ignore
)


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
            return await self.get_api()
        elif self.proxy_type == "static":
            return self.static_proxy  # type: ignore
        else:
            return None

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
