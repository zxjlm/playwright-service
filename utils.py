#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.com
@Create Time: 2025-04-17 15:47:57
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""

from bs4 import BeautifulSoup
import re


def clean_html_utils(html: str, parser: str = "html.parser") -> str:
    """
    clean html, reduce token count while keep important information

    Args:
        html: original html content
        parser: BeautifulSoup parser type

    Returns:
        cleaned html content
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, parser)

    # remove scripts, styles, noscript, iframe, svg, head, link
    for script in soup(
        ["script", "style", "noscript", "iframe", "svg", "head", "link"]
    ):
        script.decompose()

    # remove html comments
    comments = soup.find_all(
        string=lambda text: isinstance(text, str) and text.strip().startswith("<!--")
    )
    for comment in comments:
        comment.extract()

    # remove hidden elements
    for hidden in soup.find_all(
        style=re.compile(r"display:\s*none|visibility:\s*hidden")
    ):
        hidden.decompose()

    # remove media tags
    for media in soup(["img", "video", "audio", "canvas"]):
        media.decompose()

    # remove javascript links
    for a_tag in soup.find_all("a", href=re.compile(r"javascript:")):
        a_tag.decompose()

    # clean div tags (keep content)
    for div in soup.find_all("div"):
        div.unwrap()

    # clean input tags (keep content)
    for input in soup.find_all("input"):
        input.unwrap()

    # clean span tags (keep content)
    for span in soup.find_all("span"):
        span.unwrap()

    # clean tag attributes, only keep necessary attributes
    for tag in soup.find_all():
        if tag.attrs:
            allowed_attrs = ["href", "src", "alt", "title"]
            attrs_to_remove = [attr for attr in tag.attrs if attr not in allowed_attrs]
            for attr in attrs_to_remove:
                del tag.attrs[attr]

    return str(soup)


if __name__ == "__main__":
    with open("./test_data/baidu.html", "r") as f:
        html = f.read()
    print(clean_html_utils(html))
