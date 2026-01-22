#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-01-22
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Enhanced browser functionality API endpoints
All Rights Reserved.
"""

from fastapi import APIRouter, HTTPException, Depends
from utils.loggers import logger
from apis.deps import get_request_id
from schemas.enhanced_schema import (
    EnhancedPageInfoRequest,
    EnhancedPageInfoResponse,
    ExecuteScriptRequest,
    ExecuteScriptResponse,
    PageMetricsRequest,
    PageMetricsResponse,
    PerformanceMetrics,
    PageSize,
    InteractiveElement,
    NetworkRequest,
)
from browsers.browser_manager import BrowserManager

router = APIRouter(prefix="/enhanced", tags=["Enhanced Browser Features"])


@router.post("/page-info", response_model=EnhancedPageInfoResponse)
async def get_enhanced_page_info(
    request: EnhancedPageInfoRequest,
    request_id: str = Depends(get_request_id),
):
    """
    Get comprehensive page information including performance metrics,
    interactive elements, and network requests.

    This endpoint uses enhanced JavaScript injections to gather detailed
    page information that goes beyond basic HTML content.
    """
    logger.info(f"[{request_id}] Enhanced page info request for URL: {request.url}")

    browser_manager = BrowserManager()
    page = None

    try:
        # Get browser and page
        browser = await browser_manager.get_browser(
            browser_type=request.browser,
            request_id=request_id,
        )

        context = await browser.create_context(
            proxy={"server": request.proxy} if request.proxy else None,
            viewport={"width": request.viewport_width, "height": request.viewport_height},
        )

        page = await browser.create_page(context)

        # Navigate to URL
        logger.info(f"[{request_id}] Navigating to {request.url}")
        response = await page.goto(
            request.url,
            wait_until=request.wait_until,
            timeout=request.timeout * 1000,
        )

        if not response:
            raise HTTPException(status_code=500, detail="Failed to load page")

        # Wait a bit for dynamic content
        await page.wait_for_timeout(1000)

        # Get page title
        title = await page.title()
        final_url = page.url

        # Get performance metrics
        performance_data = await page.evaluate("window.getPerformanceMetrics()")
        performance = None
        if performance_data:
            performance = PerformanceMetrics(
                dns=performance_data.get("dns"),
                tcp=performance_data.get("tcp"),
                request=performance_data.get("request"),
                response=performance_data.get("response"),
                dom_processing=performance_data.get("domProcessing"),
                load_complete=performance_data.get("loadComplete"),
                total_time=performance_data.get("totalTime"),
            )

        # Get page size
        size_data = await page.evaluate("window.getPageSize()")
        page_size = PageSize(
            scroll_height=size_data["scrollHeight"],
            scroll_width=size_data["scrollWidth"],
            client_height=size_data["clientHeight"],
            client_width=size_data["clientWidth"],
            body_height=size_data["bodyHeight"],
            body_width=size_data["bodyWidth"],
        )

        # Get interactive elements
        elements_data = await page.evaluate("window.getInteractiveElements()")
        interactive_elements = [
            InteractiveElement(
                tag=elem["tag"],
                selector=elem["selector"],
                text=elem["text"],
                visible=elem["visible"],
            )
            for elem in elements_data
        ]

        # Get network requests
        requests_data = await page.evaluate("window.getNetworkRequests()")
        network_requests = [
            NetworkRequest(
                name=req["name"],
                type=req["type"],
                duration=req["duration"],
                size=req["size"],
                start_time=req["startTime"],
            )
            for req in requests_data
        ]

        # Check if resources are done loading
        resources_done = await page.evaluate("window.checkResourcesDone()")

        logger.info(f"[{request_id}] Successfully gathered enhanced page info")

        return EnhancedPageInfoResponse(
            url=request.url,
            final_url=final_url,
            title=title,
            performance=performance,
            page_size=page_size,
            interactive_elements=interactive_elements,
            network_requests=network_requests,
            resources_done=resources_done,
        )

    except Exception as e:
        logger.error(f"[{request_id}] Error getting enhanced page info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if page:
            await page.close()


@router.post("/execute-script", response_model=ExecuteScriptResponse)
async def execute_custom_script(
    request: ExecuteScriptRequest,
    request_id: str = Depends(get_request_id),
):
    """
    Execute custom JavaScript on a page and return the result.

    This endpoint allows you to run arbitrary JavaScript code on the page
    after it has loaded, enabling custom data extraction and manipulation.
    """
    logger.info(f"[{request_id}] Script execution request for URL: {request.url}")

    browser_manager = BrowserManager()
    page = None

    try:
        # Get browser and page
        browser = await browser_manager.get_browser(
            browser_type=request.browser,
            request_id=request_id,
        )

        context = await browser.create_context(
            proxy={"server": request.proxy} if request.proxy else None,
            viewport={"width": request.viewport_width, "height": request.viewport_height},
        )

        page = await browser.create_page(context)

        # Navigate to URL
        logger.info(f"[{request_id}] Navigating to {request.url}")
        response = await page.goto(
            request.url,
            wait_until=request.wait_until,
            timeout=request.timeout * 1000,
        )

        if not response:
            raise HTTPException(status_code=500, detail="Failed to load page")

        # Wait before executing if specified
        if request.wait_before_execute > 0:
            await page.wait_for_timeout(int(request.wait_before_execute * 1000))

        # Execute the custom script
        logger.info(f"[{request_id}] Executing custom script")
        result = await page.evaluate(request.script)

        logger.info(f"[{request_id}] Script executed successfully")

        return ExecuteScriptResponse(
            url=request.url,
            result=result,
            error=None,
        )

    except Exception as e:
        logger.error(f"[{request_id}] Error executing script: {str(e)}")
        return ExecuteScriptResponse(
            url=request.url,
            result=None,
            error=str(e),
        )
    finally:
        if page:
            await page.close()


@router.post("/metrics", response_model=PageMetricsResponse)
async def get_page_metrics(
    request: PageMetricsRequest,
    request_id: str = Depends(get_request_id),
):
    """
    Get specific page metrics based on request parameters.

    This endpoint allows you to selectively request only the metrics
    you need, reducing processing time and response size.
    """
    logger.info(f"[{request_id}] Page metrics request for URL: {request.url}")

    browser_manager = BrowserManager()
    page = None

    try:
        # Get browser and page
        browser = await browser_manager.get_browser(
            browser_type=request.browser,
            request_id=request_id,
        )

        context = await browser.create_context(
            proxy={"server": request.proxy} if request.proxy else None,
        )

        page = await browser.create_page(context)

        # Navigate to URL
        logger.info(f"[{request_id}] Navigating to {request.url}")
        response = await page.goto(
            request.url,
            wait_until=request.wait_until,
            timeout=request.timeout * 1000,
        )

        if not response:
            raise HTTPException(status_code=500, detail="Failed to load page")

        # Wait a bit for dynamic content
        await page.wait_for_timeout(1000)

        final_url = page.url

        # Get performance metrics if requested
        performance = None
        if request.include_performance:
            performance_data = await page.evaluate("window.getPerformanceMetrics()")
            if performance_data:
                performance = PerformanceMetrics(
                    dns=performance_data.get("dns"),
                    tcp=performance_data.get("tcp"),
                    request=performance_data.get("request"),
                    response=performance_data.get("response"),
                    dom_processing=performance_data.get("domProcessing"),
                    load_complete=performance_data.get("loadComplete"),
                    total_time=performance_data.get("totalTime"),
                )

        # Get network requests if requested
        network_requests = None
        if request.include_network:
            requests_data = await page.evaluate("window.getNetworkRequests()")
            network_requests = [
                NetworkRequest(
                    name=req["name"],
                    type=req["type"],
                    duration=req["duration"],
                    size=req["size"],
                    start_time=req["startTime"],
                )
                for req in requests_data
            ]

        # Get interactive elements if requested
        interactive_elements = None
        if request.include_interactions:
            elements_data = await page.evaluate("window.getInteractiveElements()")
            interactive_elements = [
                InteractiveElement(
                    tag=elem["tag"],
                    selector=elem["selector"],
                    text=elem["text"],
                    visible=elem["visible"],
                )
                for elem in elements_data
            ]

        # Get page size
        size_data = await page.evaluate("window.getPageSize()")
        page_size = PageSize(
            scroll_height=size_data["scrollHeight"],
            scroll_width=size_data["scrollWidth"],
            client_height=size_data["clientHeight"],
            client_width=size_data["clientWidth"],
            body_height=size_data["bodyHeight"],
            body_width=size_data["bodyWidth"],
        )

        # Check if resources are done loading
        resources_done = await page.evaluate("window.checkResourcesDone()")

        logger.info(f"[{request_id}] Successfully gathered page metrics")

        return PageMetricsResponse(
            url=request.url,
            final_url=final_url,
            performance=performance,
            network_requests=network_requests,
            interactive_elements=interactive_elements,
            page_size=page_size,
            resources_done=resources_done,
        )

    except Exception as e:
        logger.error(f"[{request_id}] Error getting page metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if page:
            await page.close()
