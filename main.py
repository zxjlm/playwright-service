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
from proxy import Proxy
from utils import clean_html_utils
from config import browser_context_manager

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    logger.info("Application shutdown event triggered")
    await shutdown_browsers()


async def cleanup_browsers():

    while True:
        await asyncio.sleep(60)  # 每分钟检查一次
        if (
            browser_context_manager.last_request_time
            and datetime.now() - browser_context_manager.last_request_time
            > timedelta(minutes=10)
        ):
            logger.info("No requests for 10 minutes, cleaning up browsers")
            await shutdown_browsers()
            break


async def shutdown_browsers():

    logger.info("Shutting down browsers")
    if browser_context_manager.chrome_browser:
        await browser_context_manager.chrome_browser.close()
        browser_context_manager.chrome_browser = None
    if browser_context_manager.firefox_browser:
        await browser_context_manager.firefox_browser.close()
        browser_context_manager.firefox_browser = None
    logger.info("Browsers shutdown completed")


async def create_context(
    browser: Browser, proxy: ProxySettings | None = None
) -> BrowserContext:
    context = await browser.new_context(ignore_https_errors=True, proxy=proxy)
    await context.route(
        "**/*.{png,jpg,jpeg,gif,svg,mp3,mp4,avi,flac,ogg,wav,webm}",
        handler=lambda route, request: route.abort(),
    )
    return context
