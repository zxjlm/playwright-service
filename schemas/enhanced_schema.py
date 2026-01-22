#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-01-22
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Enhanced browser functionality schemas
All Rights Reserved.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PerformanceMetrics(BaseModel):
    """Page performance metrics"""

    dns: Optional[float] = Field(None, description="DNS lookup time (ms)")
    tcp: Optional[float] = Field(None, description="TCP connection time (ms)")
    request: Optional[float] = Field(None, description="Request time (ms)")
    response: Optional[float] = Field(None, description="Response time (ms)")
    dom_processing: Optional[float] = Field(None, description="DOM processing time (ms)")
    load_complete: Optional[float] = Field(None, description="Load complete time (ms)")
    total_time: Optional[float] = Field(None, description="Total load time (ms)")


class PageSize(BaseModel):
    """Page size metrics"""

    scroll_height: int = Field(..., description="Scroll height")
    scroll_width: int = Field(..., description="Scroll width")
    client_height: int = Field(..., description="Client height")
    client_width: int = Field(..., description="Client width")
    body_height: int = Field(..., description="Body height")
    body_width: int = Field(..., description="Body width")


class InteractiveElement(BaseModel):
    """Interactive element information"""

    tag: str = Field(..., description="Element tag name")
    selector: str = Field(..., description="CSS selector")
    text: str = Field(..., description="Element text content (truncated)")
    visible: bool = Field(..., description="Whether element is visible")


class NetworkRequest(BaseModel):
    """Network request information"""

    name: str = Field(..., description="Request URL")
    type: str = Field(..., description="Resource type")
    duration: float = Field(..., description="Request duration (ms)")
    size: int = Field(..., description="Transfer size (bytes)")
    start_time: float = Field(..., description="Start time relative to page load")


class EnhancedPageInfoRequest(BaseModel):
    """Request model for enhanced page info"""

    url: str = Field(..., description="URL to visit")
    browser: Optional[str] = Field("chrome", description="Browser type (chrome, firefox, webkit)")
    timeout: Optional[int] = Field(30, description="Timeout in seconds")
    wait_until: Optional[str] = Field("networkidle", description="Wait until state")
    viewport_width: Optional[int] = Field(1920, description="Viewport width")
    viewport_height: Optional[int] = Field(1080, description="Viewport height")
    proxy: Optional[str] = Field(None, description="Proxy URL")


class EnhancedPageInfoResponse(BaseModel):
    """Response model for enhanced page info"""

    url: str = Field(..., description="Requested URL")
    final_url: str = Field(..., description="Final URL after redirects")
    title: str = Field(..., description="Page title")
    performance: Optional[PerformanceMetrics] = Field(None, description="Performance metrics")
    page_size: Optional[PageSize] = Field(None, description="Page size metrics")
    interactive_elements: List[InteractiveElement] = Field(
        default_factory=list, description="Interactive elements on page"
    )
    network_requests: List[NetworkRequest] = Field(
        default_factory=list, description="Network requests made"
    )
    resources_done: bool = Field(..., description="Whether all resources are loaded")


class ExecuteScriptRequest(BaseModel):
    """Request model for script execution"""

    url: str = Field(..., description="URL to visit")
    script: str = Field(..., description="JavaScript code to execute")
    browser: Optional[str] = Field("chrome", description="Browser type (chrome, firefox, webkit)")
    timeout: Optional[int] = Field(30, description="Timeout in seconds")
    wait_until: Optional[str] = Field("networkidle", description="Wait until state")
    viewport_width: Optional[int] = Field(1920, description="Viewport width")
    viewport_height: Optional[int] = Field(1080, description="Viewport height")
    proxy: Optional[str] = Field(None, description="Proxy URL")
    wait_before_execute: Optional[float] = Field(0, description="Wait time before execution (seconds)")


class ExecuteScriptResponse(BaseModel):
    """Response model for script execution"""

    url: str = Field(..., description="Requested URL")
    result: Any = Field(..., description="Script execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")


class PageMetricsRequest(BaseModel):
    """Request model for page metrics"""

    url: str = Field(..., description="URL to visit")
    browser: Optional[str] = Field("chrome", description="Browser type (chrome, firefox, webkit)")
    timeout: Optional[int] = Field(30, description="Timeout in seconds")
    wait_until: Optional[str] = Field("networkidle", description="Wait until state")
    include_performance: bool = Field(True, description="Include performance metrics")
    include_network: bool = Field(True, description="Include network requests")
    include_interactions: bool = Field(True, description="Include interactive elements")
    proxy: Optional[str] = Field(None, description="Proxy URL")


class PageMetricsResponse(BaseModel):
    """Response model for page metrics"""

    url: str = Field(..., description="Requested URL")
    final_url: str = Field(..., description="Final URL after redirects")
    performance: Optional[PerformanceMetrics] = Field(None, description="Performance metrics")
    network_requests: Optional[List[NetworkRequest]] = Field(None, description="Network requests")
    interactive_elements: Optional[List[InteractiveElement]] = Field(
        None, description="Interactive elements"
    )
    page_size: Optional[PageSize] = Field(None, description="Page size")
    resources_done: bool = Field(..., description="Whether all resources are loaded")
