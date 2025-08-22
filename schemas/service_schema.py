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
    browser_type: typing.Literal["chrome", "firefox"] = Field(default="chrome")
    headers: dict = Field(default_factory=dict)
    timeout: int = Field(default=10000, ge=1000, le=100000)
    wait_until: typing.Literal["domcontentloaded", "networkidle", "load", "commit"] = (
        Field(default="domcontentloaded")
    )
    is_force_get_content: bool = Field(default=False, description="")
    # need_proxy: bool = Field(
    #     default=False, description=""
    # )  # ATT: switch proxy will reduce context performance


class CleanHtmlInput(BaseModel):
    html: str
    parser: str = Field(default="html.parser")


class HtmlResponse(BaseModel):
    html: str
    page_status_code: typing.Union[int, str]
    page_error: str


class CleanHtmlResponse(BaseModel):
    html: str
