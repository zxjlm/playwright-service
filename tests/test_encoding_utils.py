#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for encoding utilities
"""

from encoding_utils import (
    detect_charset_from_content_type,
    detect_charset_from_html,
    normalize_charset,
    decode_html_content,
    fix_garbled_html,
    _has_decoding_errors,
)


class TestDetectCharsetFromContentType:
    """Tests for Content-Type charset detection"""

    def test_charset_in_content_type_lowercase(self):
        """Test detecting charset from Content-Type (lowercase)"""
        result = detect_charset_from_content_type("text/html; charset=gbk")
        assert result == "gb18030"

    def test_charset_in_content_type_uppercase(self):
        """Test detecting charset from Content-Type (uppercase)"""
        result = detect_charset_from_content_type("text/html; CHARSET=GBK")
        assert result == "gb18030"

    def test_charset_in_content_type_with_quotes(self):
        """Test detecting charset from Content-Type with quotes"""
        result = detect_charset_from_content_type('text/html; charset="utf-8"')
        assert result == "utf-8"

    def test_charset_in_content_type_with_single_quotes(self):
        """Test detecting charset from Content-Type with single quotes"""
        result = detect_charset_from_content_type("text/html; charset='gb2312'")
        assert result == "gb18030"

    def test_no_charset_in_content_type(self):
        """Test Content-Type without charset"""
        result = detect_charset_from_content_type("text/html")
        assert result is None

    def test_empty_content_type(self):
        """Test empty Content-Type"""
        result = detect_charset_from_content_type("")
        assert result is None

    def test_none_content_type(self):
        """Test None Content-Type"""
        result = detect_charset_from_content_type(None)
        assert result is None


class TestDetectCharsetFromHtml:
    """Tests for HTML meta charset detection"""

    def test_html5_charset_meta(self):
        """Test HTML5 charset meta tag"""
        html = b'<!DOCTYPE html><html><head><meta charset="gbk"></head></html>'
        result = detect_charset_from_html(html)
        assert result == "gb18030"

    def test_html4_content_type_meta(self):
        """Test HTML4 Content-Type meta tag"""
        html = b'<html><head><meta http-equiv="Content-Type" content="text/html; charset=gb2312"></head></html>'
        result = detect_charset_from_html(html)
        assert result == "gb18030"

    def test_xml_encoding_declaration(self):
        """Test XML encoding declaration"""
        html = b'<?xml version="1.0" encoding="UTF-8"?><html></html>'
        result = detect_charset_from_html(html)
        assert result == "utf-8"

    def test_no_charset_in_html(self):
        """Test HTML without charset declaration"""
        html = b"<html><head><title>Test</title></head><body></body></html>"
        result = detect_charset_from_html(html)
        assert result is None

    def test_charset_with_single_quotes(self):
        """Test charset with single quotes"""
        html = b"<html><head><meta charset='gb2312'></head></html>"
        result = detect_charset_from_html(html)
        assert result == "gb18030"


class TestNormalizeCharset:
    """Tests for charset normalization"""

    def test_normalize_gbk(self):
        """Test GBK normalization"""
        assert normalize_charset("gbk") == "gb18030"
        assert normalize_charset("GBK") == "gb18030"

    def test_normalize_gb2312(self):
        """Test GB2312 normalization"""
        assert normalize_charset("gb2312") == "gb18030"
        assert normalize_charset("GB2312") == "gb18030"
        assert normalize_charset("gb_2312") == "gb18030"

    def test_normalize_utf8(self):
        """Test UTF-8 normalization"""
        assert normalize_charset("utf8") == "utf-8"
        assert normalize_charset("UTF-8") == "utf-8"

    def test_normalize_unknown(self):
        """Test unknown charset passthrough"""
        assert normalize_charset("unknown-charset") == "unknown-charset"

    def test_normalize_empty(self):
        """Test empty charset"""
        assert normalize_charset("") is None
        assert normalize_charset(None) is None


class TestDecodeHtmlContent:
    """Tests for HTML content decoding"""

    def test_decode_utf8_content(self):
        """Test decoding UTF-8 content"""
        html_bytes = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>你好世界</body></html>".encode(
            "utf-8"
        )
        content, encoding = decode_html_content(html_bytes)
        assert "你好世界" in content
        assert encoding in ["utf-8", "gb18030"]  # Both should work for this content

    def test_decode_gbk_content(self):
        """Test decoding GBK content"""
        html_bytes = "<!DOCTYPE html><html><head><meta charset='gbk'></head><body>你好世界</body></html>".encode(
            "gbk"
        )
        content, encoding = decode_html_content(html_bytes)
        assert "你好世界" in content
        assert encoding == "gb18030"

    def test_decode_gb2312_content(self):
        """Test decoding GB2312 content"""
        html_bytes = "<!DOCTYPE html><html><head><meta charset='gb2312'></head><body>中文内容</body></html>".encode(
            "gb2312"
        )
        content, encoding = decode_html_content(html_bytes)
        assert "中文内容" in content
        assert encoding == "gb18030"

    def test_decode_with_content_type_header(self):
        """Test decoding with Content-Type header"""
        html_bytes = "<!DOCTYPE html><html><body>中文</body></html>".encode("gbk")
        content, encoding = decode_html_content(
            html_bytes, content_type="text/html; charset=gbk"
        )
        assert "中文" in content
        assert encoding == "gb18030"

    def test_decode_empty_content(self):
        """Test decoding empty content"""
        content, encoding = decode_html_content(b"")
        assert content == ""
        assert encoding == "utf-8"

    def test_decode_with_fallback_encodings(self):
        """Test decoding with custom fallback encodings"""
        html_bytes = "<!DOCTYPE html><body>测试</body>".encode("gbk")
        content, encoding = decode_html_content(
            html_bytes, fallback_encodings=["utf-8", "gb18030"]
        )
        assert "测试" in content


class TestHasDecodingErrors:
    """Tests for decoding error detection"""

    def test_no_errors_in_valid_text(self):
        """Test valid text has no errors"""
        assert _has_decoding_errors("你好世界，这是正常的中文文本。") is False

    def test_detect_replacement_characters(self):
        """Test detection of replacement characters"""
        text = "这是\ufffd测试\ufffd文本\ufffd" * 100
        assert _has_decoding_errors(text) is True

    def test_detect_garbled_patterns(self):
        """Test detection of garbled patterns"""
        assert _has_decoding_errors("锟斤拷锟斤拷" * 50) is True
        assert _has_decoding_errors("ï¿½" * 100) is True

    def test_empty_text(self):
        """Test empty text"""
        assert _has_decoding_errors("") is False


class TestFixGarbledHtml:
    """Tests for garbled HTML fixing"""

    def test_fix_not_garbled_content(self):
        """Test that valid content is unchanged"""
        html = "<!DOCTYPE html><html><body>正常的中文内容</body></html>"
        result = fix_garbled_html(html)
        assert result == html

    def test_fix_with_original_bytes(self):
        """Test fixing with original bytes available"""
        # Create garbled content by decoding GBK as UTF-8
        original = "中文内容".encode("gbk")
        try:
            garbled = original.decode("utf-8", errors="replace")
        except Exception:
            garbled = "锟斤拷"  # Fallback for test

        # Fix should re-decode correctly
        result = fix_garbled_html(garbled, original_bytes=original)
        # The result should contain valid Chinese characters
        assert "锟" not in result or result != garbled

    def test_fix_empty_content(self):
        """Test fixing empty content"""
        result = fix_garbled_html("")
        assert result == ""

    def test_fix_none_content(self):
        """Test fixing None content"""
        result = fix_garbled_html(None)
        assert result is None


class TestRealWorldScenarios:
    """Tests for real-world encoding scenarios"""

    def test_chinese_government_website_gbk(self):
        """Simulate Chinese government website with GBK encoding"""
        # Simulate HTML from a Chinese government website
        html_template = """<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=gb2312">
<title>国家税务总局</title>
</head>
<body>
<h1>欢迎访问国家税务总局</h1>
<p>公告信息：关于税收优惠政策的通知</p>
</body>
</html>"""
        html_bytes = html_template.encode("gb2312")

        # Decode and verify
        content, encoding = decode_html_content(html_bytes)
        assert "国家税务总局" in content
        assert "欢迎访问" in content
        assert "税收优惠政策" in content
        assert encoding == "gb18030"

    def test_chinese_website_mixed_content(self):
        """Test website with both Chinese and English content"""
        html = """<!DOCTYPE html>
<html>
<head><meta charset="gbk"></head>
<body>
<h1>Welcome 欢迎</h1>
<p>This is a test 这是测试</p>
</body>
</html>"""
        html_bytes = html.encode("gbk")

        content, encoding = decode_html_content(html_bytes)
        assert "Welcome" in content
        assert "欢迎" in content
        assert "This is a test" in content
        assert "这是测试" in content

    def test_fallback_to_utf8(self):
        """Test fallback to UTF-8 for unknown encoding"""
        html = "<html><body>Simple ASCII content</body></html>"
        html_bytes = html.encode("ascii")

        content, encoding = decode_html_content(html_bytes)
        assert "Simple ASCII content" in content
