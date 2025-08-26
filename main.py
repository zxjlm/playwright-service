from contextlib import asynccontextmanager
from fastapi import FastAPI
from playwright.async_api import (
    Browser,
    BrowserContext,
    ProxySettings,
)
from loguru import logger
from fastapi_mcp import FastApiMCP

from browsers import browser_manager
from apis.service_router import service_router
from apis.mcp_router import mcp_router

app = FastAPI()

mcp = FastApiMCP(app)

app.include_router(service_router)

mcp.mount_http(mcp_router)


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
