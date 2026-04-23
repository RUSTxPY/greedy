/*! FFI helpers for C ABI compatibility
 * 
 * Safe wrappers for unsafe C string operations.
 */

use std::ffi::{CStr, CString};
use std::os::raw::c_char;

/// Safely free a C string allocated by this library.
/// 
/// # Safety
/// - `ptr` must have been allocated by CString::into_raw
/// - `ptr` must not be null
/// - `ptr` must not be freed twice
pub unsafe fn free_cstring(ptr: *mut c_char) {
    if !ptr.is_null() {
        // Reconstruct CString to drop it properly
        let _ = CString::from_raw(ptr);
    }
}

/// Convert a C string to a Rust string slice.
/// 
/// # Safety
/// - `ptr` must be a valid null-terminated UTF-8 string
/// - Returns None if not valid UTF-8
pub unsafe fn cstr_to_str(ptr: *const c_char) -> Option<&'static str> {
    if ptr.is_null() {
        return None;
    }
    
    CStr::from_ptr(ptr).to_str().ok()
}

/// Convert a Rust string to a newly allocated C string.
/// 
/// Returns null on allocation failure (extremely rare).
pub fn str_to_cstring(s: &str) -> *mut c_char {
    match CString::new(s) {
        Ok(cstring) => cstring.into_raw(),
        Err(_) => std::ptr::null_mut(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cstr_to_str_valid() {
        let cstring = CString::new("hello").unwrap();
        let ptr = cstring.as_ptr();
        
        unsafe {
            assert_eq!(cstr_to_str(ptr), Some("hello"));
        }
    }

    #[test]
    fn test_cstr_to_str_null() {
        unsafe {
            assert_eq!(cstr_to_str(std::ptr::null()), None);
        }
    }

    #[test]
    fn test_str_to_cstring() {
        let ptr = str_to_cstring("test");
        assert!(!ptr.is_null());
        
        unsafe {
            free_cstring(ptr);
        }
    }

    #[test]
    fn test_free_null() {
        unsafe {
            free_cstring(std::ptr::null_mut());
        }
    }
}
