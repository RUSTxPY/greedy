"""Native shared library loader using ctypes.

Tries to load platform-specific shared library for text normalization.
Falls back gracefully if not available.
"""

import ctypes
import logging
import platform
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class NativeLib:
    """Wrapper for native shared library."""
    
    def __init__(self, lib_path: Path):
        self._lib = ctypes.CDLL(str(lib_path))
        
        # Configure function signatures
        # ddgs_normalize_text
        self._lib.ddgs_normalize_text.argtypes = [ctypes.c_char_p]
        self._lib.ddgs_normalize_text.restype = ctypes.c_char_p
        
        # ddgs_free_string
        self._lib.ddgs_free_string.argtypes = [ctypes.c_char_p]
        self._lib.ddgs_free_string.restype = None
        
        # ddgs_health_check
        self._lib.ddgs_health_check.argtypes = []
        self._lib.ddgs_health_check.restype = ctypes.c_int
        
        # ddgs_rank_similarity
        self._lib.ddgs_rank_similarity.argtypes = [
            ctypes.c_char_p,                 # query
            ctypes.c_int,                    # min_token_length
            ctypes.c_int,                    # count
            ctypes.POINTER(ctypes.c_char_p), # titles
            ctypes.POINTER(ctypes.c_char_p), # bodies
            ctypes.POINTER(ctypes.c_char_p), # hrefs
            ctypes.POINTER(ctypes.c_int),    # out_buckets
        ]
        self._lib.ddgs_rank_similarity.restype = ctypes.c_int
        
        # Verify library works
        if self._lib.ddgs_health_check() != 1:
            raise RuntimeError("Native library health check failed")
    
    def normalize_text(self, text: str) -> str:
        """Normalize text using native library."""
        encoded = text.encode('utf-8')
        result_ptr = self._lib.ddgs_normalize_text(encoded)
        
        if result_ptr is None:
            raise RuntimeError("Native normalization returned null")
        
        try:
            # Cast to c_char_p and decode
            char_ptr = ctypes.cast(result_ptr, ctypes.c_char_p)
            result_bytes = char_ptr.value
            if result_bytes is None:
                raise RuntimeError("Failed to read native result")
            return result_bytes.decode('utf-8')
        finally:
            self._lib.ddgs_free_string(result_ptr)

    def rank_similarity(
        self, 
        query: str, 
        min_token_length: int, 
        titles: list[str], 
        bodies: list[str], 
        hrefs: list[str]
    ) -> list[int]:
        """Rank documents using native library."""
        count = len(titles)
        if count == 0:
            return []
        
        # Prepare arrays
        c_query = query.encode('utf-8')
        
        c_titles = (ctypes.c_char_p * count)(*[s.encode('utf-8') for s in titles])
        c_bodies = (ctypes.c_char_p * count)(*[s.encode('utf-8') for s in bodies])
        c_hrefs = (ctypes.c_char_p * count)(*[s.encode('utf-8') for s in hrefs])
        
        out_buckets = (ctypes.c_int * count)()
        
        # Call native function
        res = self._lib.ddgs_rank_similarity(
            c_query,
            min_token_length,
            count,
            c_titles,
            c_bodies,
            c_hrefs,
            out_buckets
        )
        
        if res != 0:
            raise RuntimeError(f"Native ranking failed with error code {res}")
        
        return list(out_buckets)


def _get_lib_name() -> Optional[str]:
    """Get platform-specific library name."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Normalize architecture names
    if machine in ('amd64', 'x86_64'):
        arch = 'amd64'
    elif machine in ('arm64', 'aarch64'):
        arch = 'arm64'
    else:
        return None
    
    if system == 'linux':
        return f"libddgs_native_linux_{arch}.so"
    elif system == 'darwin':
        return f"libddgs_native_macos_{arch}.dylib"
    elif system == 'windows':
        return f"ddgs_native_windows_{arch}.dll"
    
    return None


def _find_library() -> Optional[Path]:
    """Find native library in package data."""
    lib_name = _get_lib_name()
    if not lib_name:
        logger.debug("Unsupported platform: %s %s", platform.system(), platform.machine())
        return None
    
    # Look in package data directory
    package_dir = Path(__file__).parent
    data_dir = package_dir / "data"
    lib_path = data_dir / lib_name
    
    if lib_path.exists():
        logger.debug("Found native library: %s", lib_path)
        return lib_path
    
    # Try development path (native/target/release/)
    dev_path = package_dir.parent / "native" / "target" / "release" / lib_name
    if dev_path.exists():
        logger.debug("Found development native library: %s", dev_path)
        return dev_path
    
    logger.debug("Native library not found: %s", lib_name)
    return None


# Global library instance (lazy loaded)
_native_lib: Optional[NativeLib] = None
_NATIVE_AVAILABLE = False


def _load_native() -> bool:
    """Attempt to load native library. Returns True if successful."""
    global _native_lib, _NATIVE_AVAILABLE
    
    if _NATIVE_AVAILABLE and _native_lib is not None:
        return True
    
    lib_path = _find_library()
    if not lib_path:
        return False
    
    try:
        _native_lib = NativeLib(lib_path)
        _NATIVE_AVAILABLE = True
        logger.info("Loaded native library from %s", lib_path)
        return True
    except Exception as e:
        logger.debug("Failed to load native library: %s", e)
        _NATIVE_AVAILABLE = False
        return False


def is_native_available() -> bool:
    """Check if native library is available and working."""
    return _load_native()


def normalize_text_native(text: str) -> str:
    """Normalize text using native library.
    
    Raises:
        RuntimeError: If native library is not available.
    """
    if not _load_native():
        raise RuntimeError("Native library not available")
    
    return _native_lib.normalize_text(text)


def rank_similarity_native(
    query: str, 
    min_token_length: int, 
    titles: list[str], 
    bodies: list[str], 
    hrefs: list[str]
) -> list[int]:
    """Rank documents using native library.
    
    Raises:
        RuntimeError: If native library is not available.
    """
    if not _load_native():
        raise RuntimeError("Native library not available")
    
    return _native_lib.rank_similarity(query, min_token_length, titles, bodies, hrefs)


__all__ = [
    'is_native_available',
    'normalize_text_native',
    'rank_similarity_native',
]
