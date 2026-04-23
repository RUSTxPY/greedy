"""Utilities with optional native acceleration."""

import logging
import re
import unicodedata
from contextlib import suppress
from datetime import datetime, timezone
from functools import lru_cache
from html import unescape
from typing import Callable, Optional
from urllib.parse import unquote

from .exceptions import DDGSException

logger = logging.getLogger(__name__)

# Try to load native library
try:
    from .utils_native import is_native_available, normalize_text_native
    _native_available = is_native_available()
except Exception as e:
    logger.debug("Native utils not available: %s", e)
    _native_available = False
    is_native_available = lambda: False
    normalize_text_native = None

# Pre-compiled regex for pure Python path
_REGEX_STRIP_TAGS = re.compile(r"<[^>]+>")


def _extract_vqd(html_bytes: bytes, query: str) -> str:
    """Extract vqd from html bytes."""
    for c1, c1_len, c2 in (
        (b'vqd="', 5, b'"'),
        (b"vqd=", 4, b"&"),
        (b"vqd='", 5, b"'"),
    ):
        with suppress(ValueError):
            start = html_bytes.index(c1) + c1_len
            end = html_bytes.index(c2, start)
            return html_bytes[start:end].decode()

    msg = f"_extract_vqd() {query=} Could not extract vqd."
    raise DDGSException(msg)


def _normalize_url(url: str) -> str:
    """Unquote URL and replace spaces with '+'."""
    return unquote(url).replace(" ", "+") if url else ""


# Cache for common strings (pure Python only)
@lru_cache(maxsize=2048)
def _normalize_text_cached(raw: str) -> str:
    """Cached version for repeated strings."""
    return _normalize_text_python_impl(raw)


def _normalize_text_python_impl(raw: str) -> str:
    """Pure Python implementation - optimized single-pass.
    
    Same logic as Rust, but optimized Python.
    """
    if not raw:
        return ""
    
    # 1. Strip HTML tags (pre-compiled regex)
    text = _REGEX_STRIP_TAGS.sub("", raw)
    
    # 2. Unescape HTML entities
    text = unescape(text)
    
    # 3. Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)
    
    # 4-5. Remove control chars + collapse whitespace (single pass)
    result = []
    append = result.append  # Local variable for speed
    last_was_space = True
    
    for ch in text:
        cat = unicodedata.category(ch)
        
        # Skip control characters (Cc category), except common whitespace
        if cat == 'Cc' and ch not in '\t\n\r':
            continue
        
        # Check if whitespace (Zs, Zl, Zp categories, or other whitespace)
        if cat.startswith('Z') or ch.isspace():
            if not last_was_space:
                append(' ')
                last_was_space = True
        else:
            append(ch)
            last_was_space = False
    
    # Remove trailing space
    if result and result[-1] == ' ':
        result.pop()
    
    return ''.join(result)


def _normalize_text_python(raw: str) -> str:
    """Normalize using optimized Python with caching."""
    if not raw:
        return ""
    
    # Use cache for reasonable-sized strings
    if len(raw) < 2000:
        return _normalize_text_cached(raw)
    
    return _normalize_text_python_impl(raw)


def _normalize_text(raw: str) -> str:
    """Normalize text using best available implementation.
    
    Priority:
    1. Native shared library (20-50x speedup)
    2. Optimized pure Python (baseline, always works)
    
    Args:
        raw: Input string to normalize.
        
    Returns:
        Normalized string.
    """
    if not raw:
        return ""
    
    # Try native first if available
    if _native_available and normalize_text_native:
        try:
            return normalize_text_native(raw)
        except Exception as e:
            logger.debug("Native normalize failed, falling back: %s", e)
            # Fall through to Python
    
    # Pure Python fallback (always works)
    return _normalize_text_python(raw)


def get_normalization_backend() -> str:
    """Return current backend name ('native' or 'python')."""
    if _native_available:
        return "native"
    return "python"


def _normalize_date(date: int | str) -> str:
    """Normalize date from integer to ISO format if applicable."""
    return datetime.fromtimestamp(date, timezone.utc).isoformat() if isinstance(date, int) else date


def _expand_proxy_tb_alias(proxy: str | None) -> str | None:
    """Expand "tb" to a full proxy URL if applicable."""
    return "socks5h://127.0.0.1:9150" if proxy == "tb" else proxy
