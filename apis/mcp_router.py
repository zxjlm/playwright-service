#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-26 10:23:22
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""
import io
from fastapi import APIRouter
from markitdown import MarkItDown

from apis.utils import get_html_base
from schemas.service_schema import UrlInput, HtmlResponse, MarkdownResponse
from apis.deps import SessionDep

mcp_router = APIRouter(prefix="/mcp", tags=["mcp"])


@mcp_router.post(
    "/html", operation_id="playwright_service:get_html", response_model=HtmlResponse
)
async def get_html(url_input: UrlInput, session: SessionDep):
    result = await get_html_base(url_input, session)
    return result


@mcp_router.post(
    "/markdown",
    operation_id="playwright_service:get_markdown",
    response_model=MarkdownResponse,
)
async def get_markdown(url_input: UrlInput, session: SessionDep):
    result = await get_html_base(url_input, session)
    md = MarkItDown(enable_plugins=False)  # Set to True to enable plugins
    html_bytes = result.html.encode("utf-8")
    html_file_like = io.BytesIO(html_bytes)
    markdown_result = md.convert_stream(html_file_like, file_extension=".html")
    result = MarkdownResponse(
        markdown=markdown_result.text_content,
        page_status_code=result.page_status_code,
        page_error=result.page_error,
    )
    return result
