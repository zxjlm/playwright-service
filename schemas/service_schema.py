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


class UrlInput(BaseModel):
    url: HttpUrl
    browser_type: typing.Literal["chrome", "firefox", "webkit"] = Field(
        default="chrome"
    )
    headers: dict = Field(default_factory=dict)
    timeout: int = Field(default=10000, ge=1000, le=100000)
    wait_until: typing.Literal["domcontentloaded", "networkidle", "load", "commit"] = (
        Field(default="domcontentloaded")
    )
    is_force_get_content: bool = Field(
        default=False,
        description="force get content from url, ignore the error of wait_until",
    )
    use_cache: bool = Field(
        default=True, description="use cache to get content from url"
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
