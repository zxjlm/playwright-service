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
from fastapi import APIRouter

# from markitdown import MarkItDown
import html2text
import markdownify

from apis.utils import get_html_base
from schemas.service_schema import (
    MarkdownInput,
    UrlInput,
    HtmlResponse,
    MarkdownResponse,
)
from apis.deps import SessionDep
from utils import clean_html_utils

mcp_router = APIRouter(prefix="/mcp", tags=["mcp"])


@mcp_router.post(
    "/html",
    operation_id="playwright_service:get_html",
    response_model=HtmlResponse,
    # dependencies=[Depends(verify_bearauth)],
)
async def get_html(url_input: UrlInput, session: SessionDep):
    result = await get_html_base(url_input, session)
    return result


@mcp_router.post(
    "/markdown",
    operation_id="playwright_service:get_markdown",
    response_model=MarkdownResponse,
    # dependencies=[Depends(verify_bearauth)],
)
async def get_markdown(markdown_input: MarkdownInput, session: SessionDep):
    result = await get_html_base(markdown_input, session)

    # base on markitdown
    # md = MarkItDown(enable_plugins=False)  # Set to True to enable plugins
    # html_bytes = result.html.encode("utf-8")
    # html_file_like = io.BytesIO(html_bytes)
    # markdown_result = md.convert_stream(html_file_like, file_extension=".html")

    # pre clean html
    result.html = clean_html_utils(result.html)

    # base on html2text
    if markdown_input.parser == "html2text":
        h = html2text.HTML2Text()
        markdown_result = h.handle(result.html)

    # base on markdownify
    elif markdown_input.parser == "markdownify":
        markdown_result = markdownify.markdownify(result.html)

    else:
        markdown_result = result.html

    result = MarkdownResponse(
        markdown=markdown_result,
        page_status_code=result.page_status_code,
        page_error=result.page_error,
        cache_hit=result.cache_hit,
    )
    return result
