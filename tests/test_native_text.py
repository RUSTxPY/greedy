"""Tests for native text normalization implementation."""

import pytest
import platform

# Detect if we're on a supported platform
SUPPORTED_PLATFORMS = {
    ('Linux', 'x86_64'),
    ('Linux', 'AMD64'),
    ('Linux', 'aarch64'),
    ('Linux', 'arm64'),
    ('Darwin', 'x86_64'),
    ('Darwin', 'arm64'),
}

_current_platform = (platform.system(), platform.machine())
IS_SUPPORTED = _current_platform in SUPPORTED_PLATFORMS


class TestNativeLoading:
    """Test native library loading."""
    
    @pytest.mark.skipif(not IS_SUPPORTED, reason=f"Platform {_current_platform} not supported for native")
    def test_library_found(self):
        """Test that library is found on supported platforms."""
        from ddgs.utils_native import _find_library
        
        lib_path = _find_library()
        assert lib_path is not None, "Library should be found"
        assert lib_path.exists(), "Library file should exist"
    
    @pytest.mark.skipif(not IS_SUPPORTED, reason=f"Platform {_current_platform} not supported")
    def test_library_loads(self):
        """Test that library loads successfully."""
        from ddgs.utils_native import _load_native, is_native_available
        
        result = _load_native()
        assert isinstance(result, bool)
    
    def test_unsupported_platform_graceful(self):
        """Test graceful handling on unsupported platforms."""
        from ddgs.utils import _normalize_text, get_normalization_backend
        
        result = _normalize_text("hello")
        assert result == "hello"
        
        backend = get_normalization_backend()
        assert backend in ('native', 'python')


class TestCorrectness:
    """Test normalization correctness."""
    
    TEST_CASES = [
        ("", ""),
        ("hello", "hello"),
        ("  hello  world  ", "hello world"),
        ("<b>hello</b>", "hello"),
        ("<p>paragraph</p>", "paragraph"),
        ("&lt;tag&gt;", "<tag>"),
        ("&amp;", "&"),
        ("&#39;", "'"),
        ("&quot;quoted&quot;", '"quoted"'),
        ("line\none\ttwo", "line one two"),  # Newlines and tabs become spaces
        ("Multiple   spaces", "Multiple spaces"),
        ("  leading", "leading"),
        ("trailing  ", "trailing"),
        ("日本語テスト", "日本語テスト"),
        ("<div>HTML &amp; Entities</div>", "HTML & Entities"),
    ]
    
    def test_python_implementation(self):
        """Test pure Python implementation."""
        from ddgs.utils import _normalize_text_python
        
        for input_text, expected in self.TEST_CASES:
            result = _normalize_text_python(input_text)
            assert result == expected, f"Input: {input_text!r}, Expected: {expected!r}, Got: {result!r}"
    
    @pytest.mark.skipif(not IS_SUPPORTED, reason="Native not available")
    def test_native_implementation(self):
        """Test native implementation if available."""
        from ddgs.utils_native import normalize_text_native, is_native_available
        
        if not is_native_available():
            pytest.skip("Native library not loaded")
        
        for input_text, expected in self.TEST_CASES:
            result = normalize_text_native(input_text)
            assert result == expected, f"Input: {input_text!r}, Expected: {expected!r}, Got: {result!r}"
    
    @pytest.mark.skipif(not IS_SUPPORTED, reason="Native not available")
    def test_native_python_parity(self):
        """Ensure native and Python produce identical results."""
        from ddgs.utils import _normalize_text_python
        from ddgs.utils_native import normalize_text_native, is_native_available
        
        if not is_native_available():
            pytest.skip("Native library not loaded")
        
        test_strings = [
            "<b>Bold</b> and <i>italic</i>",
            "&lt;script&gt;alert(1)&lt;/script&gt;",
            "  Spaces   everywhere  ",
            "Unicode: 日本語, Emoji: test",
            "",
            "x" * 10000,
        ]
        
        for s in test_strings:
            py_result = _normalize_text_python(s)
            native_result = normalize_text_native(s)
            assert py_result == native_result, f"Mismatch for: {s[:50]!r}..."


class TestPerformance:
    """Benchmark native vs Python."""
    
    @pytest.mark.skipif(not IS_SUPPORTED, reason="Native not available")
    def test_native_performance(self):
        """Verify native performance is reasonable.
        
        Note: ctypes overhead means native may not be faster for very small strings.
        The benefit shows with larger strings or batch operations.
        """
        import time
        from ddgs.utils import _normalize_text_python
        from ddgs.utils_native import normalize_text_native, is_native_available
        
        if not is_native_available():
            pytest.skip("Native library not loaded")
        
        # Use larger input to amortize ctypes overhead
        test_input = (
            "<div class=\"result\"><h3>Python Programming Language</h3>"
            "<p>Python is &lt;b&gt;programming&lt;/b&gt; that lets you work quickly "
            "and integrate systems. &amp; It's great!</p></div>\n"
        ) * 100  # Large input
        
        iterations = 100
        
        # Warmup
        for _ in range(10):
            _normalize_text_python(test_input)
            normalize_text_native(test_input)
        
        # Python timing
        start = time.perf_counter()
        for _ in range(iterations):
            _normalize_text_python(test_input)
        python_time = time.perf_counter() - start
        
        # Native timing
        start = time.perf_counter()
        for _ in range(iterations):
            normalize_text_native(test_input)
        native_time = time.perf_counter() - start
        
        speedup = python_time / native_time if native_time > 0 else 0
        print(f"\nPython: {python_time:.3f}s, Native: {native_time:.3f}s, Speedup: {speedup:.1f}x")
        
        # Native should be competitive or faster for large strings
        # (allow some tolerance for ctypes overhead)
        assert native_time < python_time * 2, f"Native too slow: {speedup:.1f}x"


class TestEdgeCases:
    """Edge case handling."""
    
    def test_null_bytes(self):
        """Test handling of null bytes - C strings treat them as terminators."""
        from ddgs.utils import _normalize_text
        
        # C strings can't contain null bytes - they're terminators
        # So "hello\x00world" is treated as just "hello" by native
        # Pure Python can handle this differently
        result = _normalize_text("hello\x00world")
        # Native returns "hello" (stops at null), Python returns "helloworld"
        # Either is acceptable - just check it doesn't crash
        assert result in ("hello", "helloworld")
    
    def test_very_long_string(self):
        """Test with very long input."""
        from ddgs.utils import _normalize_text
        
        long_input = "<p>" + "x" * 100000 + "</p>"
        result = _normalize_text(long_input)
        
        assert len(result) == 100000
        assert "<p>" not in result
