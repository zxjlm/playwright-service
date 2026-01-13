#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:22:50
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""


import asyncio
import os
import typing
from dotenv import load_dotenv
from pathlib import Path
from loguru import logger
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import create_async_engine


BASE_DIR = Path(__file__).parent
_env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_path) and not load_dotenv(_env_path):
    logger.warning(f"{BASE_DIR} failed to load .env file")


class ServiceConfig(BaseSettings):
    proxy_type: typing.Literal["dynamic", "static", "none"] = Field(default="none")
    proxy_api_url: str | None = Field(default=None)
    proxy_check_url: str | None = Field(default=None)
    static_proxy: str | None = Field(default=None)
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/playwright_service"
    )
    playwright_browsers_url: str = Field(default="ws://localhost:9222")
    max_concurrent_requests: int = Field(default=10)
    mcp_bearer_token: str = Field(default="")

    auth_config: int = Field(default=0)

    sentry_dsn: str | None = Field(default=None)
    otlp_endpoint: str | None = Field(default=None)

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="service_")

    @model_validator(mode="after")
    def check_proxy_fields(self):
        if self.proxy_api_url and self.proxy_type == "none":
            logger.warning(
                "proxy_type is none, which will cause proxy_api_url is not used"
            )

        proxy_type = self.proxy_type
        proxy_api_url = self.proxy_api_url
        static_proxy = self.static_proxy
        if proxy_type == "dynamic" and not proxy_api_url:
            raise ValueError("when proxy_type is dynamic, proxy_api_url is required")
        if proxy_type == "static" and not static_proxy:
            raise ValueError("when proxy_type is static, static_proxy is required")
        return self


service_config = ServiceConfig()
engine = create_async_engine(service_config.database_url)
request_semaphore = asyncio.Semaphore(service_config.max_concurrent_requests)
