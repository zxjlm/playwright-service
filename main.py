from contextlib import asynccontextmanager
from html import parser
from typing import Literal
import typing
from fastapi import FastAPI
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PWTimeoutError,
    ProxySettings,
)
import asyncio
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime, timedelta
from loguru import logger


from get_error import get_error
from utils import clean_html_utils
from browsers import browser_manager
from apis.service_router import service_router

app = FastAPI()
app.include_router(service_router, prefix="/service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    logger.info("Application shutdown event triggered")
    await shutdown_browsers()


async def shutdown_browsers():
    """Shutdown all browsers"""
    logger.info("Shutting down browsers")
    await browser_manager.cleanup_all_browsers()
    logger.info("Browsers shutdown completed")


async def create_context(
    browser: Browser, proxy: ProxySettings | None = None
) -> BrowserContext:
    """Create browser context (maintain backward compatibility)"""
    context = await browser.new_context(ignore_https_errors=True, proxy=proxy)
    await context.route(
        "**/*.{png,jpg,jpeg,gif,svg,mp3,mp4,avi,flac,ogg,wav,webm}",
        handler=lambda route, request: route.abort(),
    )
    return context
