/*! DDGS Native - Fast text normalization for Python
 * 
 * Provides C ABI for Python ctypes integration.
 * Organized into modules for maintainability.
 */

mod ffi;
mod normalize;
mod similarity;
mod utils;

use std::ffi::CStr;
use std::os::raw::{c_char, c_int};

/// Rank similarity FFI.
/// 
/// # Safety
/// - titles, bodies, hrefs must be arrays of count valid null-terminated UTF-8 strings.
/// - out_buckets must have space for count c_int.
#[no_mangle]
pub unsafe extern "C" fn ddgs_rank_similarity(
    query: *const c_char,
    min_token_length: c_int,
    count: c_int,
    titles: *const *const c_char,
    bodies: *const *const c_char,
    hrefs: *const *const c_char,
    out_buckets: *mut c_int,
) -> c_int {
    if query.is_null() || titles.is_null() || bodies.is_null() || hrefs.is_null() || out_buckets.is_null() || count <= 0 {
        return -1;
    }

    let query_str = match CStr::from_ptr(query).to_str() {
        Ok(s) => s,
        Err(_) => return -1,
    };

    let title_ptrs = std::slice::from_raw_parts(titles, count as usize);
    let body_ptrs = std::slice::from_raw_parts(bodies, count as usize);
    let href_ptrs = std::slice::from_raw_parts(hrefs, count as usize);
    let output = std::slice::from_raw_parts_mut(out_buckets, count as usize);

    let mut title_strs = Vec::with_capacity(count as usize);
    let mut body_strs = Vec::with_capacity(count as usize);
    let mut href_strs = Vec::with_capacity(count as usize);

    for i in 0..count as usize {
        title_strs.push(CStr::from_ptr(title_ptrs[i]).to_str().unwrap_or(""));
        body_strs.push(CStr::from_ptr(body_ptrs[i]).to_str().unwrap_or(""));
        href_strs.push(CStr::from_ptr(href_ptrs[i]).to_str().unwrap_or(""));
    }

    similarity::rank_similarity(
        query_str,
        min_token_length as usize,
        &title_strs,
        &body_strs,
        &href_strs,
        output,
    );

    0 // Success
}

/// Normalize text: strip HTML, unescape entities, NFC normalize,
/// remove control chars, collapse whitespace.
/// 
/// Uses thread-local static buffer to avoid cross-allocator issues.
/// Safe for Python GIL (single-threaded per interpreter).
/// 
/// # Safety
/// - `input` must be a valid null-terminated UTF-8 string
/// - Returns null on error (invalid UTF-8)
/// - Returned pointer is valid until next call on same thread
#[no_mangle]
pub unsafe extern "C" fn ddgs_normalize_text(input: *const c_char) -> *const c_char {
    if input.is_null() {
        return std::ptr::null();
    }
    
    let c_str = match CStr::from_ptr(input).to_str() {
        Ok(s) => s,
        Err(_) => return std::ptr::null(),
    };
    
    let result = normalize::normalize_text(c_str);
    
    // Store in thread-local buffer with null terminator
    thread_local! {
        static BUFFER: std::cell::RefCell<Vec<u8>> = std::cell::RefCell::new(Vec::with_capacity(8192));
    }
    
    BUFFER.with(|buf| {
        let mut buf = buf.borrow_mut();
        buf.clear();
        buf.extend_from_slice(result.as_bytes());
        buf.push(0); // null terminator
        buf.as_ptr() as *const c_char
    })
}

/// Free function - no-op for static buffer version.
/// Kept for API compatibility.
#[no_mangle]
pub unsafe extern "C" fn ddgs_free_string(_ptr: *mut c_char) {
    // No-op: using static buffer
}

/// Check if library is working.
#[no_mangle]
pub extern "C" fn ddgs_health_check() -> c_int {
    1
}

/// Get version string.
/// 
/// # Safety
/// Caller must NOT free the returned pointer (it's static).
#[no_mangle]
pub unsafe extern "C" fn ddgs_version() -> *const c_char {
    static VERSION: &str = "0.1.0\0";
    VERSION.as_ptr() as *const c_char
}
// test change
// test change
