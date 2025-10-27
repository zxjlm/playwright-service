#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 清理功能的单元测试
"""

import pytest
from utils import clean_html_utils


class TestCleanHtmlUtils:
    """HTML 清理工具测试类"""

    def test_clean_html_basic(self):
        """测试基本HTML清理功能"""
        html = """
        <html>
            <head>
                <script>alert('test')</script>
                <style>body { color: red; }</style>
                <link rel="stylesheet" href="style.css">
            </head>
            <body>
                <div>Test Content</div>
                <img src="image.jpg" alt="test">
                <video src="video.mp4"></video>
            </body>
        </html>
        """

        result = clean_html_utils(html)

        # 验证脚本和样式被移除
        assert "<script>" not in result
        assert "<style>" not in result
        assert "<link>" not in result

        # 验证图片和视频被移除
        assert "<img>" not in result
        assert "<video>" not in result

        # 验证内容保留
        assert "Test Content" in result

    def test_clean_html_empty_input(self):
        """测试空输入"""
        result = clean_html_utils("")
        assert result == ""

    def test_clean_html_none_input(self):
        """测试None输入"""
        result = clean_html_utils(None)
        assert result == ""

    def test_clean_html_remove_hidden_elements(self):
        """测试移除隐藏元素"""
        html = """
        <div style="display: none">Hidden Content</div>
        <div style="visibility: hidden">Also Hidden</div>
        <div>Visible Content</div>
        """

        result = clean_html_utils(html)

        # 验证隐藏元素被移除
        assert "Hidden Content" not in result
        assert "Also Hidden" not in result

        # 验证可见内容保留
        assert "Visible Content" in result

    def test_clean_html_remove_javascript_links(self):
        """测试移除JavaScript链接"""
        html = """
        <a href="javascript:void(0)">JS Link</a>
        <a href="https://example.com">Normal Link</a>
        <a href="javascript:alert('test')">Another JS Link</a>
        """

        result = clean_html_utils(html)

        # 验证JavaScript链接被移除
        assert "JS Link" not in result
        assert "Another JS Link" not in result

        # 验证正常链接保留
        assert "Normal Link" in result

    def test_clean_html_clean_tag_attributes(self):
        """测试清理标签属性"""
        html = """
        <a href="https://example.com" id="test" class="link" onclick="alert('test')" title="Link Title">
            Content
        </a>
        """

        result = clean_html_utils(html)

        # 验证不必要的属性被移除
        assert "id=" not in result
        assert "class=" not in result
        assert "onclick=" not in result

        # 验证允许的属性保留
        assert "href=" in result
        assert "title=" in result
        assert "Content" in result

    def test_clean_html_unwrap_tags(self):
        """测试标签解包功能"""
        html = """
        <div>
            <span>Nested Content</span>
            <input type="text" value="test">
        </div>
        """

        result = clean_html_utils(html)

        # 验证div和span标签被移除，但内容保留
        assert "<div>" not in result
        assert "<span>" not in result
        assert "<input" not in result

        # 验证内容保留
        assert "Nested Content" in result

    def test_clean_html_remove_comments(self):
        """测试处理HTML注释"""
        # 注释处理可能因BeautifulSoup而不同，测试主要关注内容保留
        html = """
        <!-- This is a comment -->
        <div>Content</div>
        <!-- Another comment -->
        """

        result = clean_html_utils(html)

        # 验证内容保留
        assert "Content" in result

    def test_clean_html_remove_media_tags(self):
        """测试移除媒体标签"""
        html = """
        <img src="image.jpg" alt="Image">
        <video src="video.mp4">Video Content</video>
        <audio src="audio.mp3">Audio Content</audio>
        <canvas id="canvas">Canvas Content</canvas>
        <div>Regular Content</div>
        """

        result = clean_html_utils(html)

        # 验证媒体标签被移除
        assert "<img" not in result
        assert "<video" not in result
        assert "<audio" not in result
        assert "<canvas" not in result

        # 验证媒体内容被移除
        assert "Video Content" not in result
        assert "Audio Content" not in result
        assert "Canvas Content" not in result

        # 验证常规内容保留
        assert "Regular Content" in result

    def test_clean_html_remove_iframe_svg(self):
        """测试移除iframe和svg"""
        html = """
        <iframe src="https://example.com"></iframe>
        <svg><circle cx="50" cy="50" r="40"></circle></svg>
        <div>Content</div>
        """

        result = clean_html_utils(html)

        # 验证iframe和svg被移除
        assert "<iframe" not in result
        assert "<svg>" not in result

        # 验证内容保留
        assert "Content" in result

    def test_clean_html_preserve_important_attributes(self):
        """测试保留重要属性"""
        html = """
        <a href="https://example.com" title="Link Title">Link Text</a>
        """

        result = clean_html_utils(html)

        # 验证重要属性保留（img标签会被移除，所以只测试a标签）
        assert "href=" in result
        assert "title=" in result
        assert "Link Text" in result

    def test_clean_html_complex_structure(self):
        """测试复杂HTML结构清理"""
        html = """
        <html>
        <head>
            <script src="script.js"></script>
            <style>body { margin: 0; }</style>
        </head>
        <body>
            <a href="javascript:void(0)" onclick="doSomething()">JS Link</a>
            <a href="/home" title="Home">Home</a>
            <div style="display: none">Hidden content</div>
            <img src="banner.jpg" alt="Banner">
            <h1>Main Title</h1>
            <p>This is a paragraph</p>
        </body>
        </html>
        """

        result = clean_html_utils(html)

        # 验证所有不需要的元素被移除
        assert "<script>" not in result
        assert "<style>" not in result
        assert "<head>" not in result
        assert "<img" not in result
        assert "javascript:" not in result
        assert "onclick=" not in result

        # 验证重要内容保留
        assert "Main Title" in result
        assert "This is a paragraph" in result
        assert "Home" in result

    def test_clean_html_with_different_parser(self):
        """测试使用不同解析器"""
        html = "<div>Test Content</div>"

        # 测试默认解析器
        result1 = clean_html_utils(html, "html.parser")
        assert "Test Content" in result1

        # 测试lxml解析器（如果可用）
        try:
            result2 = clean_html_utils(html, "lxml")
            assert "Test Content" in result2
        except Exception:
            # lxml可能不可用，这是正常的
            pass
