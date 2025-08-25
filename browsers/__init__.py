#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:01:55
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Browser Package Initialization File
All Rights Reserved.
"""

from .base_browser import BaseBrowser
from .chrome_browser import ChromeBrowser
from .firefox_browser import FirefoxBrowser
from .webkit_browser import WebKitBrowser
from .browser_factory import BrowserFactory
from .browser_manager import BrowserManager, browser_manager

__all__ = [
    "BaseBrowser",
    "ChromeBrowser", 
    "FirefoxBrowser",
    "WebKitBrowser",
    "BrowserFactory",
    "BrowserManager",
    "browser_manager"
]
