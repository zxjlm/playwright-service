#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:20:55
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""


import typing
from pydantic import BaseModel, Field, HttpUrl


class BaseBrowserInput(BaseModel):
    """Base class for browser input parameters shared by HTML and Screenshot operations."""

    url: HttpUrl
    browser_type: typing.Literal["chrome", "firefox", "webkit"] = Field(
        default="chrome"
    )
    headers: dict = Field(default_factory=dict)
    timeout: int = Field(default=10000, ge=1000, le=100000)
    wait_until: typing.Literal["domcontentloaded", "networkidle", "load", "commit"] = (
        Field(default="domcontentloaded")
    )
    is_force_get_content: int = Field(
        default=0,
        description="force get content from url, ignore the error of wait_until",
    )


class UrlInput(BaseBrowserInput):
    use_cache: int = Field(
        default=0,
        description="use cache to get content from url. ATTENTION: the cache is only base on the url and browser type, which means if you give a longer timeout, but the content may be different because of the cached is old. So i make the cache parameter default to 0, you can set it to 1 if you want to use cache.",
    )
    use_force_html_clean: int = Field(
        default=0, description="force clean html, may cause content loss"
    )
    # need_proxy: bool = Field(
    #     default=False, description=""
    # )  # ATT: switch proxy will reduce context performance


class MarkdownInput(UrlInput):
    parser: typing.Literal["html2text", "markdownify"] = Field(default="html2text")


class CleanHtmlInput(BaseModel):
    html: str
    parser: str = Field(default="html.parser")


class HtmlResponse(BaseModel):
    html: str
    page_status_code: typing.Union[int, str]
    page_error: str
    cache_hit: int = Field(default=0)


class MarkdownResponse(BaseModel):
    markdown: str
    page_status_code: typing.Union[int, str]
    page_error: str
    cache_hit: int = Field(default=0)


class CleanHtmlResponse(BaseModel):
    html: str


class ScreenshotInput(BaseBrowserInput):
    width: int = Field(default=1920)
    height: int = Field(default=1080)
    full_page: int = Field(default=0)


class ScreenshotResponse(BaseModel):
    screenshot: str  # base64 encoded screenshot data
    page_status_code: typing.Union[int, str]
    page_error: str
