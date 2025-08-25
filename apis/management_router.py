#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:17:59
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""
from fastapi import APIRouter
from playwright.async_api import async_playwright
from config import service_config


manager_router = APIRouter(prefix="/management", tags=["management"])


# @manager_router.get("/browsers")
# async def get_browsers():
#     with async_playwright() as p:
#         browser = await p.chromium.connect(
#             service_config.playwright_browsers_url
#         )
#         return {"browsers": browser.pages}