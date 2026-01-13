from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from fastapi_mcp import FastApiMCP
from loguru import logger
from prometheus_client import make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware

from browsers import browser_manager
from base_proxy import proxy_pool
from apis.service_router import service_router
from apis.mcp_router import mcp_router
from apis.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_request_size_bytes,
    http_response_size_bytes,
    http_requests_in_flight,
)
from sentry_sdk import init

from config import service_config
from utils.middleware import RequestLoggingMiddleware


if service_config.otlp_endpoint:
    from utils.loggers import setup_otlp_logger

    setup_otlp_logger(service_config.otlp_endpoint, "playwright-service", "production")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    logger.info("Application shutdown event triggered")
    # Record proxy reuse stats before shutdown
    await proxy_pool.shutdown()
    await shutdown_browsers()


async def shutdown_browsers():
    """Shutdown all browsers"""
    logger.info("Shutting down browsers")
    await browser_manager.cleanup_all_browsers()
    logger.info("Browsers shutdown completed")


app = FastAPI(lifespan=lifespan)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Prometheus metrics collection middleware"""

    async def dispatch(self, request: Request, call_next):
        # 跳过 metrics 端点本身
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path

        # 估算请求大小（从 headers 获取 Content-Length，如果没有则设为 0）
        request_size = 0
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                request_size = int(content_length)
            except ValueError:
                request_size = 0

        # 增加活跃请求数
        http_requests_in_flight.labels(method=method, path=path).inc()

        start_time = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code

            # 记录响应大小（从 headers 获取 Content-Length）
            response_size = 0
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    response_size = int(content_length)
                except ValueError:
                    response_size = 0

            # 记录响应大小指标
            http_response_size_bytes.labels(
                method=method, path=path, status_code=status_code
            ).observe(response_size)

            return response
        except Exception as e:
            logger.exception(f"Error in request: {e}")
            status_code = 500
            raise
        finally:
            # 计算请求持续时间
            duration = time.perf_counter() - start_time

            # 减少活跃请求数
            http_requests_in_flight.labels(method=method, path=path).dec()

            # 记录指标
            http_requests_total.labels(
                method=method, path=path, status_code=status_code
            ).inc()
            http_request_duration_seconds.labels(method=method, path=path).observe(
                duration
            )
            http_request_size_bytes.labels(method=method, path=path).observe(
                request_size
            )


# 添加 Prometheus 中间件
app.add_middleware(PrometheusMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# 使用 Prometheus 官方提供的 ASGI 应用挂载 /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


mcp = FastApiMCP(
    app,
    include_tags=["mcp"],
    # auth_config=AuthConfig(
    #     dependencies=[Depends(token_auth_scheme)],
    # ),
)

app.include_router(service_router)

mcp.mount_http(mcp_router)

mcp.setup_server()

if service_config.sentry_dsn:
    init(
        dsn=service_config.sentry_dsn,
        environment="production",
        enable_tracing=True,
    )

# async def create_context(
#     browser: Browser, proxy: ProxySettings | None = None
# ) -> BrowserContext:
#     """Create browser context (maintain backward compatibility)"""
#     context = await browser.new_context(ignore_https_errors=True, proxy=proxy)
#     await context.route(
#         "**/*.{png,jpg,jpeg,gif,svg,mp3,mp4,avi,flac,ogg,wav,webm}",
#         handler=lambda route, request: route.abort(),
#     )
#     return context
