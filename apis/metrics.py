#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-01-XX XX:XX:XX
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Prometheus metrics collection module
All Rights Reserved.
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
)


# ============================================================================
# HTTP 请求指标
# ============================================================================

# HTTP 请求总数计数器
# 标签: method (HTTP方法), path (请求路径), status_code (HTTP状态码)
http_requests_total = Counter(
    "api_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)

# HTTP 请求延迟直方图
# 标签: method (HTTP方法), path (请求路径)
# 单位: 秒
http_request_duration_seconds = Histogram(
    "api_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

# HTTP 请求大小直方图
# 标签: method (HTTP方法), path (请求路径)
# 单位: 字节
http_request_size_bytes = Histogram(
    "api_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "path"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000),
)

# HTTP 响应大小直方图
# 标签: method (HTTP方法), path (请求路径), status_code (HTTP状态码)
# 单位: 字节
http_response_size_bytes = Histogram(
    "api_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "path", "status_code"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000),
)

# 当前活跃的 HTTP 请求数
# 标签: method (HTTP方法), path (请求路径)
http_requests_in_flight = Gauge(
    "api_requests_in_flight",
    "Current number of HTTP requests being processed",
    ["method", "path"],
)


# ============================================================================
# 浏览器操作指标
# ============================================================================

# 浏览器操作总数计数器
# 标签: browser_type (浏览器类型), operation (操作类型: html/screenshot)
browser_operations_total = Counter(
    "browser_operations_total",
    "Total number of browser operations",
    ["browser_type", "operation"],
)

# 浏览器操作延迟直方图
# 标签: browser_type (浏览器类型), operation (操作类型: html/screenshot)
# 单位: 秒
browser_operation_duration_seconds = Histogram(
    "browser_operation_duration_seconds",
    "Browser operation duration in seconds",
    ["browser_type", "operation"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0),
)

# 浏览器操作成功/失败计数器
# 标签: browser_type (浏览器类型), operation (操作类型), status (success/failure)
browser_operations_status_total = Counter(
    "browser_operations_status_total",
    "Total number of browser operations by status",
    ["browser_type", "operation", "status"],
)

# 浏览器页面状态码分布
# 标签: browser_type (浏览器类型), operation (操作类型), page_status_code (页面状态码)
browser_page_status_codes_total = Counter(
    "browser_page_status_codes_total",
    "Total number of browser page status codes",
    ["browser_type", "operation", "page_status_code"],
)


# ============================================================================
# 缓存指标
# ============================================================================

# 缓存命中/未命中计数器
# 标签: status (hit/miss)
cache_operations_total = Counter(
    "cache_operations_total",
    "Total number of cache operations",
    ["status"],
)


# ============================================================================
# 并发和等待指标
# ============================================================================

# 当前等待的请求数
waiting_requests = Gauge(
    "waiting_requests",
    "Current number of requests waiting for semaphore",
)

# 当前正在处理的请求数
processing_requests = Gauge(
    "processing_requests",
    "Current number of requests being processed",
)


# ============================================================================
# 代理指标
# ============================================================================

# 代理使用计数器
# 标签: proxy_type (代理类型: dynamic/static/none)
proxy_usage_total = Counter(
    "proxy_usage_total",
    "Total number of proxy usages",
    ["proxy_type"],
)

# 代理获取失败计数器
proxy_failures_total = Counter(
    "proxy_failures_total",
    "Total number of proxy acquisition failures",
)

# 代理复用统计直方图
# 记录每个代理被复用的次数，用于评估代理池质量
# 标签: proxy_type (代理类型: dynamic/static)
proxy_reuse_count = Histogram(
    "proxy_reuse_count",
    "Number of times a proxy was reused before failure",
    ["proxy_type"],
    buckets=(1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000),
)

# 代理切换计数器
# 标签: reason (切换原因: tunnel_failed/connection_refused/other)
proxy_switch_total = Counter(
    "proxy_switch_total",
    "Total number of proxy switches due to errors",
    ["reason"],
)

# 代理重试计数器
# 标签: attempt (重试次数: 1/2/3)
proxy_retry_total = Counter(
    "proxy_retry_total",
    "Total number of proxy retry attempts",
    ["attempt"],
)

# 当前活跃代理的复用次数
# 用于实时监控当前代理的使用情况
proxy_current_reuse_count = Gauge(
    "proxy_current_reuse_count",
    "Current reuse count of the active proxy",
)


# ============================================================================
# 错误指标
# ============================================================================

# 错误总数计数器
# 标签: error_type (错误类型: timeout/browser_error/proxy_error/other)
errors_total = Counter(
    "api_errors_total",
    "Total number of errors",
    ["error_type"],
)


# ============================================================================
# 浏览器管理指标
# ============================================================================

# 浏览器实例数
# 标签: browser_type (浏览器类型)
browser_instances = Gauge(
    "browser_instances",
    "Current number of browser instances",
    ["browser_type"],
)

# 浏览器重新初始化次数
# 标签: browser_type (浏览器类型)
browser_reinitializations_total = Counter(
    "browser_reinitializations_total",
    "Total number of browser reinitializations",
    ["browser_type"],
)
