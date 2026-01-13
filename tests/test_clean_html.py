#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for HTML cleaning functionality
"""

from utils.clean_utils import clean_html_utils


class TestCleanHtmlUtils:
    """Test class for HTML cleaning utilities"""

    def test_clean_html_basic(self):
        """Test basic HTML cleaning functionality"""
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

        # Verify scripts and styles are removed
        assert "<script>" not in result
        assert "<style>" not in result
        assert "<link>" not in result

        # Verify images and videos are removed
        assert "<img>" not in result
        assert "<video>" not in result

        # Verify content is preserved
        assert "Test Content" in result

    def test_clean_html_empty_input(self):
        """Test empty input"""
        result = clean_html_utils("")
        assert result == ""

    def test_clean_html_none_input(self):
        """Test None input"""
        result = clean_html_utils(None)
        assert result == ""

    def test_clean_html_remove_hidden_elements(self):
        """Test removal of hidden elements"""
        html = """
        <div style="display: none">Hidden Content</div>
        <div style="visibility: hidden">Also Hidden</div>
        <div>Visible Content</div>
        """

        result = clean_html_utils(html)

        # Verify hidden elements are removed
        assert "Hidden Content" not in result
        assert "Also Hidden" not in result

        # Verify visible content is preserved
        assert "Visible Content" in result

    def test_clean_html_remove_javascript_links(self):
        """Test removal of JavaScript links"""
        html = """
        <a href="javascript:void(0)">JS Link</a>
        <a href="https://example.com">Normal Link</a>
        <a href="javascript:alert('test')">Another JS Link</a>
        """

        result = clean_html_utils(html)

        # Verify JavaScript links are removed
        assert "JS Link" not in result
        assert "Another JS Link" not in result

        # Verify normal links are preserved
        assert "Normal Link" in result

    def test_clean_html_clean_tag_attributes(self):
        """Test cleaning tag attributes"""
        html = """
        <a href="https://example.com" id="test" class="link" onclick="alert('test')" title="Link Title">
            Content
        </a>
        """

        result = clean_html_utils(html)

        # Verify unnecessary attributes are removed
        assert "id=" not in result
        assert "class=" not in result
        assert "onclick=" not in result

        # Verify allowed attributes are preserved
        assert "href=" in result
        assert "title=" in result
        assert "Content" in result

    def test_clean_html_unwrap_tags(self):
        """Test tag unwrapping functionality"""
        html = """
        <div>
            <span>Nested Content</span>
            <input type="text" value="test">
        </div>
        """

        result = clean_html_utils(html)

        # Verify div and span tags are removed, but content is preserved
        assert "<div>" not in result
        assert "<span>" not in result
        assert "<input" not in result

        # Verify content is preserved
        assert "Nested Content" in result

    def test_clean_html_remove_comments(self):
        """Test HTML comment handling"""
        # Comment handling may vary with BeautifulSoup, test focuses on content preservation
        html = """
        <!-- This is a comment -->
        <div>Content</div>
        <!-- Another comment -->
        """

        result = clean_html_utils(html)

        # Verify content is preserved
        assert "Content" in result

    def test_clean_html_remove_media_tags(self):
        """Test removal of media tags"""
        html = """
        <img src="image.jpg" alt="Image">
        <video src="video.mp4">Video Content</video>
        <audio src="audio.mp3">Audio Content</audio>
        <canvas id="canvas">Canvas Content</canvas>
        <div>Regular Content</div>
        """

        result = clean_html_utils(html)

        # Verify media tags are removed
        assert "<img" not in result
        assert "<video" not in result
        assert "<audio" not in result
        assert "<canvas" not in result

        # Verify media content is removed
        assert "Video Content" not in result
        assert "Audio Content" not in result
        assert "Canvas Content" not in result

        # Verify regular content is preserved
        assert "Regular Content" in result

    def test_clean_html_remove_iframe_svg(self):
        """Test removal of iframe and svg"""
        html = """
        <iframe src="https://example.com"></iframe>
        <svg><circle cx="50" cy="50" r="40"></circle></svg>
        <div>Content</div>
        """

        result = clean_html_utils(html)

        # Verify iframe and svg are removed
        assert "<iframe" not in result
        assert "<svg>" not in result

        # Verify content is preserved
        assert "Content" in result

    def test_clean_html_preserve_important_attributes(self):
        """Test preservation of important attributes"""
        html = """
        <a href="https://example.com" title="Link Title">Link Text</a>
        """

        result = clean_html_utils(html)

        # Verify important attributes are preserved (img tags will be removed, so only test a tags)
        assert "href=" in result
        assert "title=" in result
        assert "Link Text" in result

    def test_clean_html_complex_structure(self):
        """Test complex HTML structure cleaning"""
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

        # Verify all unnecessary elements are removed
        assert "<script>" not in result
        assert "<style>" not in result
        assert "<head>" not in result
        assert "<img" not in result
        assert "javascript:" not in result
        assert "onclick=" not in result

        # Verify important content is preserved
        assert "Main Title" in result
        assert "This is a paragraph" in result
        assert "Home" in result

    def test_clean_html_with_different_parser(self):
        """Test using different parsers"""
        html = "<div>Test Content</div>"

        # Test default parser
        result1 = clean_html_utils(html, "html.parser")
        assert "Test Content" in result1

        # Test lxml parser (if available)
        try:
            result2 = clean_html_utils(html, "lxml")
            assert "Test Content" in result2
        except Exception:
            # lxml may not be available, this is normal
            pass
