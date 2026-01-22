#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-01-22
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Advanced browser utilities for dynamic content detection
All Rights Reserved.
"""

import asyncio
from typing import Optional, Dict, List
from patchright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.loggers import logger
from .browser_scripts import DOM_LOAD_HOOK, get_vue_dom_load_hook, STYLE_PATCH


class DynamicContentWaiter:
    """
    Advanced utility for waiting for dynamically loaded content.

    This implements the hook-based waiting mechanism from demo/browser.py
    for detecting when SPA frameworks (Vue.js, React, etc.) finish rendering.
    """

    HOOK_ELEMENT_PREFIX = "pw-tider"

    @staticmethod
    async def inject_dom_load_hook(page: Page) -> bool:
        """
        Inject the DOM load hook script into the page.

        This creates a hidden input element that serves as a marker
        for page load completion.

        Returns:
            bool: True if injection succeeded, False otherwise
        """
        try:
            await page.add_script_tag(content=DOM_LOAD_HOOK)
            return True
        except Exception as e:
            logger.warning(f"Failed to inject DOM load hook: {e}")
            # Page might have redirected, try again
            await page.wait_for_timeout(500)
            try:
                await page.add_script_tag(content=DOM_LOAD_HOOK)
                return True
            except Exception as e2:
                logger.error(f"Failed to inject DOM load hook (second attempt): {e2}")
                return False

    @staticmethod
    async def wait_for_hook(
        page: Page,
        hook_name: Optional[str] = None,
        timeout: int = 30000,
        raise_for_timeout: bool = True,
    ) -> bool:
        """
        Wait for a specific hook element to appear.

        Args:
            page: Playwright page object
            hook_name: Name of the hook to wait for (None for main hook)
            timeout: Timeout in milliseconds
            raise_for_timeout: Whether to raise exception on timeout

        Returns:
            bool: True if hook appeared, False if timed out
        """
        # Generate hook element ID
        if hook_name:
            import hashlib
            hook_id = hashlib.md5(hook_name.encode()).hexdigest()
            identity = f"{DynamicContentWaiter.HOOK_ELEMENT_PREFIX}-{hook_id}"
        else:
            identity = DynamicContentWaiter.HOOK_ELEMENT_PREFIX

        try:
            # Wait for the hook element to appear
            locator = page.locator(f"#{identity}")
            await locator.wait_for(state="attached", timeout=timeout)

            # Remove the hook element after detection
            await locator.evaluate("(ele) => { if (ele) ele.remove(); }")

            # Small delay to ensure stability
            await page.wait_for_timeout(100)

            logger.debug(f"Hook '{hook_name or 'main'}' detected and removed")
            return True

        except PlaywrightTimeoutError as e:
            logger.warning(
                f"Timeout waiting for hook '{hook_name or 'main'}' "
                f"(timeout={timeout}ms)"
            )
            if raise_for_timeout:
                raise e
            return False

    @staticmethod
    async def wait_for_dynamic_content(
        page: Page,
        timeout: int = 30000,
        inject_hook: bool = True,
        raise_for_timeout: bool = False,
    ) -> bool:
        """
        Wait for dynamic content to finish loading.

        This is the main method to use for SPA applications.

        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds
            inject_hook: Whether to inject the hook script
            raise_for_timeout: Whether to raise exception on timeout

        Returns:
            bool: True if content loaded, False if timed out
        """
        if inject_hook:
            success = await DynamicContentWaiter.inject_dom_load_hook(page)
            if not success:
                logger.warning("Hook injection failed, falling back to networkidle")
                await page.wait_for_load_state("networkidle", timeout=timeout)
                return True

        # Wait for the main hook
        return await DynamicContentWaiter.wait_for_hook(
            page=page,
            hook_name=None,
            timeout=timeout,
            raise_for_timeout=raise_for_timeout,
        )

    @staticmethod
    async def wait_for_all_frames(
        page: Page,
        hooked_frames: Dict[object, List[str]],
        timeout: int = 30000,
        wait_for_main: bool = True,
        raise_for_timeout: bool = False,
    ) -> None:
        """
        Wait for all hooked frames to finish loading.

        This is equivalent to wait_for_hooked_frames() in demo/browser.py.

        Args:
            page: Playwright page object
            hooked_frames: Dict mapping frames to list of script names
            timeout: Timeout in milliseconds
            wait_for_main: Whether to wait for main frame hook
            raise_for_timeout: Whether to raise exception on timeout
        """
        for frame_obj, script_names in hooked_frames.items():
            # Remove duplicates
            script_names = list(set(script_names))

            # If this is the main frame and we should wait for it
            if wait_for_main and hasattr(frame_obj, 'url'):
                if frame_obj.url == page.url:
                    script_names.append(None)  # Add main hook

            # Wait for each hook
            for script_name in script_names:
                try:
                    await DynamicContentWaiter.wait_for_hook(
                        page=page,
                        hook_name=script_name,
                        timeout=timeout,
                        raise_for_timeout=raise_for_timeout,
                    )
                except PlaywrightTimeoutError:
                    if raise_for_timeout:
                        raise
                    logger.warning(f"Timeout waiting for script: {script_name}")


class ScreenshotEnhancer:
    """
    Enhanced screenshot utilities with style manipulation.
    """

    @staticmethod
    async def prepare_page_for_screenshot(page: Page) -> None:
        """
        Prepare page for full-page screenshot by removing style constraints.

        This applies the STYLE_PATCH to ensure complete page capture.
        """
        # Add style tag to override body constraints
        await page.add_style_tag(
            content='body { height: "" !important; width: "" !important; }'
        )

        # Execute style patch script
        await page.evaluate(STYLE_PATCH)

        logger.debug("Page prepared for screenshot")

    @staticmethod
    async def take_enhanced_screenshot(
        page: Page,
        path: str,
        width: int = 1920,
        height: int = 1080,
        selector: Optional[str] = None,
        timeout: int = 0,
        full_page: bool = True,
    ) -> bytes:
        """
        Take an enhanced screenshot with automatic style fixes.

        Args:
            page: Playwright page object
            path: Path to save screenshot
            width: Viewport width
            height: Viewport height
            selector: Optional CSS selector for element screenshot
            timeout: Timeout for element wait
            full_page: Whether to capture full page

        Returns:
            bytes: Screenshot data
        """
        # Set viewport
        await page.set_viewport_size({"width": width, "height": height})

        # Prepare page
        await ScreenshotEnhancer.prepare_page_for_screenshot(page)

        # Take screenshot
        if selector:
            # Screenshot specific element
            element = page.locator(selector)
            if timeout > 0:
                await element.wait_for(timeout=timeout)
            screenshot_data = await element.screenshot(path=path)
        else:
            # Full page screenshot
            screenshot_data = await page.screenshot(path=path, full_page=full_page)

        logger.info(f"Screenshot saved to {path}")
        return screenshot_data


class ResourceMonitor:
    """
    Monitor page resource loading and dynamic content.
    """

    @staticmethod
    async def wait_until_resources_stable(
        page: Page,
        check_interval: int = 500,
        max_checks: int = 10,
        timeout: int = 30000,
    ) -> bool:
        """
        Wait until page resources are stable (no new resources loading).

        Args:
            page: Playwright page object
            check_interval: Milliseconds between checks
            max_checks: Maximum number of checks
            timeout: Total timeout in milliseconds

        Returns:
            bool: True if resources are stable, False if timed out
        """
        start_time = asyncio.get_event_loop().time()
        stable_count = 0

        while stable_count < 3:  # Require 3 consecutive stable checks
            # Check if timeout exceeded
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            if elapsed > timeout:
                logger.warning("Timeout waiting for resources to stabilize")
                return False

            # Check if resources are done
            resources_done = await page.evaluate("window.checkResourcesDone()")

            if resources_done:
                stable_count += 1
            else:
                stable_count = 0

            # Wait before next check
            await page.wait_for_timeout(check_interval)

        logger.debug("Resources are stable")
        return True

    @staticmethod
    async def get_resource_summary(page: Page) -> Dict:
        """
        Get summary of page resources.

        Returns:
            Dict with resource counts, sizes, and timing info
        """
        requests = await page.evaluate("window.getNetworkRequests()")

        # Categorize resources
        by_type = {}
        total_size = 0
        total_duration = 0

        for req in requests:
            req_type = req.get("type", "other")
            if req_type not in by_type:
                by_type[req_type] = {"count": 0, "size": 0, "duration": 0}

            by_type[req_type]["count"] += 1
            by_type[req_type]["size"] += req.get("size", 0)
            by_type[req_type]["duration"] += req.get("duration", 0)

            total_size += req.get("size", 0)
            total_duration = max(total_duration, req.get("startTime", 0) + req.get("duration", 0))

        return {
            "total_requests": len(requests),
            "total_size_bytes": total_size,
            "total_duration_ms": total_duration,
            "by_type": by_type,
        }


# Export utilities
__all__ = [
    'DynamicContentWaiter',
    'ScreenshotEnhancer',
    'ResourceMonitor',
]
