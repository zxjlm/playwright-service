#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-12-31
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: Encoding utilities for handling non-UTF-8 encoded web pages
All Rights Reserved.
"""

import re
from typing import Optional, Tuple
from loguru import logger


def detect_charset_from_content_type(content_type: Optional[str]) -> Optional[str]:
    """
    Extract charset from Content-Type header.
    
    Args:
        content_type: Content-Type header value, e.g. "text/html; charset=gbk"
        
    Returns:
        Charset string or None if not found
    """
    if not content_type:
        return None
    
    # Match charset in Content-Type header
    match = re.search(r'charset=([^\s;]+)', content_type, re.IGNORECASE)
    if match:
        charset = match.group(1).strip('"\'')
        return normalize_charset(charset)
    
    return None


def detect_charset_from_html(html_bytes: bytes) -> Optional[str]:
    """
    Detect charset from HTML meta tags in raw bytes.
    
    Args:
        html_bytes: Raw HTML content as bytes
        
    Returns:
        Charset string or None if not found
    """
    # First decode as latin-1 to safely search the bytes (latin-1 maps bytes 1:1)
    try:
        html_sample = html_bytes[:4096].decode('latin-1', errors='ignore')
    except Exception:
        return None
    
    # Common patterns for charset declaration in HTML
    patterns = [
        # HTML5: <meta charset="utf-8">
        r'<meta[^>]+charset=["\']?([^"\'>\s;]+)',
        # HTML4: <meta http-equiv="Content-Type" content="text/html; charset=gbk">
        r'<meta[^>]+content=["\'][^"\']*charset=([^"\';\s]+)',
        # XML declaration: <?xml version="1.0" encoding="gbk"?>
        r'<\?xml[^>]+encoding=["\']([^"\']+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_sample, re.IGNORECASE)
        if match:
            charset = match.group(1).strip()
            normalized = normalize_charset(charset)
            if normalized:
                return normalized
    
    return None


def normalize_charset(charset: str) -> Optional[str]:
    """
    Normalize charset name to Python codec name.
    
    Args:
        charset: Original charset name
        
    Returns:
        Normalized charset name for Python codecs
    """
    if not charset:
        return None
    
    charset = charset.lower().strip()
    
    # Common charset mappings
    charset_mappings = {
        'gb2312': 'gb18030',  # gb18030 is superset of gb2312 and gbk
        'gbk': 'gb18030',
        'gb_2312': 'gb18030',
        'gb-2312': 'gb18030',
        'chinese': 'gb18030',
        'cp936': 'gb18030',
        'ms936': 'gb18030',
        'windows-936': 'gb18030',
        'utf8': 'utf-8',
        'utf-8': 'utf-8',
        'iso-8859-1': 'latin-1',
        'latin1': 'latin-1',
        'ascii': 'ascii',
        'big5': 'big5',
        'big5-hkscs': 'big5hkscs',
        'euc-cn': 'gb18030',
        'euc-jp': 'euc-jp',
        'shift_jis': 'shift_jis',
        'shift-jis': 'shift_jis',
        'sjis': 'shift_jis',
        'euc-kr': 'euc-kr',
        'iso-2022-jp': 'iso-2022-jp',
    }
    
    return charset_mappings.get(charset, charset)


def decode_html_content(
    html_bytes: bytes,
    content_type: Optional[str] = None,
    fallback_encodings: Optional[list] = None
) -> Tuple[str, str]:
    """
    Decode HTML content from bytes with proper encoding detection.
    
    This function tries to detect the correct encoding from:
    1. Content-Type header
    2. HTML meta charset declaration
    3. Fallback encodings list
    4. UTF-8 as last resort
    
    Args:
        html_bytes: Raw HTML content as bytes
        content_type: Optional Content-Type header value
        fallback_encodings: Optional list of fallback encodings to try
        
    Returns:
        Tuple of (decoded_html_string, detected_encoding)
    """
    if not html_bytes:
        return "", "utf-8"
    
    if fallback_encodings is None:
        # Common encodings for Chinese websites
        fallback_encodings = ['gb18030', 'gbk', 'gb2312', 'big5', 'utf-8']
    
    detected_encoding = None
    
    # Step 1: Try to get charset from Content-Type header
    charset_from_header = detect_charset_from_content_type(content_type)
    if charset_from_header:
        detected_encoding = charset_from_header
        logger.debug(f"Detected encoding from Content-Type header: {detected_encoding}")
    
    # Step 2: Try to get charset from HTML meta tags
    if not detected_encoding:
        charset_from_html = detect_charset_from_html(html_bytes)
        if charset_from_html:
            detected_encoding = charset_from_html
            logger.debug(f"Detected encoding from HTML meta tag: {detected_encoding}")
    
    # Step 3: Try detected encoding first
    if detected_encoding:
        try:
            decoded = html_bytes.decode(detected_encoding)
            # Verify the decoding looks valid (no replacement characters in high ratio)
            if not _has_decoding_errors(decoded):
                return decoded, detected_encoding
        except (UnicodeDecodeError, LookupError) as e:
            logger.debug(f"Failed to decode with detected encoding {detected_encoding}: {e}")
    
    # Step 4: Try fallback encodings
    for encoding in fallback_encodings:
        try:
            decoded = html_bytes.decode(encoding)
            if not _has_decoding_errors(decoded):
                logger.debug(f"Successfully decoded with fallback encoding: {encoding}")
                return decoded, encoding
        except (UnicodeDecodeError, LookupError):
            continue
    
    # Step 5: Last resort - decode as UTF-8 with error replacement
    logger.warning("All encoding attempts failed, using UTF-8 with error replacement")
    return html_bytes.decode('utf-8', errors='replace'), 'utf-8'


def _has_decoding_errors(text: str, threshold: float = 0.05) -> bool:
    """
    Check if decoded text has signs of encoding errors.
    
    Args:
        text: Decoded text to check
        threshold: Maximum ratio of suspicious characters allowed
        
    Returns:
        True if text appears to have decoding errors
    """
    if not text:
        return False
    
    # Check for common signs of encoding errors
    # Unicode replacement character
    replacement_count = text.count('\ufffd')
    
    # Common garbled patterns when GBK is decoded as UTF-8
    # These are mojibake patterns
    garbled_patterns = ['锟斤拷', '锟', 'ï¿½', 'â€', 'Ã©', 'Ã¨', 'Ã¯']
    garbled_count = sum(text.count(p) for p in garbled_patterns)
    
    total_suspicious = replacement_count + garbled_count
    sample_length = min(len(text), 10000)  # Check first 10000 chars
    
    if sample_length > 0:
        ratio = total_suspicious / sample_length
        return ratio > threshold
    
    return False


def fix_garbled_html(html: str, original_bytes: Optional[bytes] = None) -> str:
    """
    Attempt to fix garbled HTML content.
    
    If original_bytes is provided, will try to re-decode with correct encoding.
    Otherwise, will attempt to detect and fix common mojibake patterns.
    
    Args:
        html: Potentially garbled HTML string
        original_bytes: Optional original bytes for re-decoding
        
    Returns:
        Fixed HTML string
    """
    if not html:
        return html
    
    # Check if content appears garbled
    if not _has_decoding_errors(html):
        return html
    
    # If we have original bytes, try to re-decode
    if original_bytes:
        fixed_html, encoding = decode_html_content(original_bytes)
        if not _has_decoding_errors(fixed_html):
            logger.info(f"Fixed garbled HTML by re-decoding with {encoding}")
            return fixed_html
    
    # Try to fix common mojibake patterns (GBK -> UTF-8 -> GBK)
    try:
        # This handles the case where GBK was mistakenly decoded as Latin-1 or UTF-8
        fixed = html.encode('latin-1', errors='replace').decode('gb18030', errors='replace')
        if not _has_decoding_errors(fixed) and fixed != html:
            logger.info("Fixed garbled HTML using latin-1 -> gb18030 conversion")
            return fixed
    except Exception:
        pass
    
    return html
