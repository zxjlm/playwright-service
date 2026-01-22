#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for main app MCP (FastMCP) and REST route registration.

Verifies that the migration from fastapi-mcp to fastmcp correctly registers:
- MCP protocol at /mcp
- REST /mcp/html and /mcp/markdown
"""

import pytest


def test_main_app_has_mcp_and_rest_routes():
    """Main app must expose /mcp (MCP), /mcp/html and /mcp/markdown (REST)."""
    from main import app

    paths = [r.path for r in app.router.routes if hasattr(r, "path")]
    assert "/mcp" in paths, "MCP protocol route /mcp must exist"
    assert "/mcp/html" in paths, "REST /mcp/html must exist"
    assert "/mcp/markdown" in paths, "REST /mcp/markdown must exist"
