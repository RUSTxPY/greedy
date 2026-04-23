/*! Text normalization logic
 * 
 * Main normalization pipeline:
 * 1. Strip HTML tags
 * 2. Decode HTML entities
 * 3. Unicode NFC normalization
 * 4. Remove control characters
 * 5. Collapse whitespace
 */

use once_cell::sync::Lazy;
use regex::Regex;
use unicode_normalization::UnicodeNormalization;

// Pre-compiled regex for HTML tag stripping
static HTML_TAG_RE: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"<[^>]+>").expect("valid regex pattern")
});

/// Normalize text through the full pipeline.
pub fn normalize_text(raw: &str) -> String {
    if raw.is_empty() {
        return String::new();
    }

    // Step 1: Strip HTML tags
    let text = strip_html_tags(raw);
    
    // Step 2: Decode HTML entities
    let text = decode_html_entities(&text);
    
    // Step 3: Unicode NFC normalization
    let text: String = text.nfc().collect();
    
    // Steps 4-5: Remove control chars + collapse whitespace (single pass)
    clean_whitespace(&text)
}

/// Strip HTML tags from text.
fn strip_html_tags(text: &str) -> String {
    HTML_TAG_RE.replace_all(text, "").into_owned()
}

/// Decode HTML entities (e.g., &lt; -> <, &amp; -> &).
fn decode_html_entities(text: &str) -> String {
    html_escape::decode_html_entities(text).into_owned()
}

/// Remove control characters and collapse whitespace.
/// Single-pass implementation for efficiency.
fn clean_whitespace(text: &str) -> String {
    let mut result = String::with_capacity(text.len());
    let mut last_was_space = true; // Start true to trim leading whitespace
    
    for ch in text.chars() {
        // Skip control characters (Cc category), except common whitespace
        if is_control_char(ch) {
            continue;
        }
        
        if ch.is_whitespace() {
            if !last_was_space {
                result.push(' ');
                last_was_space = true;
            }
        } else {
            result.push(ch);
            last_was_space = false;
        }
    }
    
    // Trim trailing space
    if result.ends_with(' ') {
        result.pop();
    }
    
    result
}

/// Check if a character is a control character (excluding common whitespace).
#[inline]
fn is_control_char(ch: char) -> bool {
    ch.is_control() && !matches!(ch, '\t' | '\n' | '\r')
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty() {
        assert_eq!(normalize_text(""), "");
    }

    #[test]
    fn test_no_changes() {
        assert_eq!(normalize_text("hello world"), "hello world");
    }

    #[test]
    fn test_strip_html() {
        assert_eq!(normalize_text("<b>hello</b>"), "hello");
        assert_eq!(normalize_text("<p>paragraph</p>"), "paragraph");
        assert_eq!(normalize_text("<a href='test'>link</a>"), "link");
    }

    #[test]
    fn test_decode_entities() {
        assert_eq!(normalize_text("&lt;tag&gt;"), "<tag>");
        assert_eq!(normalize_text("&amp;"), "&");
        assert_eq!(normalize_text("&#39;"), "'");
        assert_eq!(normalize_text("&quot;"), "\"");
    }

    #[test]
    fn test_whitespace_collapse() {
        assert_eq!(normalize_text("  hello  world  "), "hello world");
        assert_eq!(normalize_text("multiple   spaces"), "multiple spaces");
        assert_eq!(normalize_text("\t\ttab\t\t"), "tab");
        assert_eq!(normalize_text("\n\nnewline\n\n"), "newline");
    }

    #[test]
    fn test_control_chars() {
        assert_eq!(normalize_text("\x00"), "");
        assert_eq!(normalize_text("hello\x00world"), "helloworld");
        assert_eq!(normalize_text("\x01\x02test\x03\x04"), "test");
    }

    #[test]
    fn test_unicode_nfc() {
        // e + combining acute accent should become é
        let input = "caf\u{0065}\u{0301}";
        let result = normalize_text(input);
        assert_eq!(result, "caf\u{00e9}");
    }

    #[test]
    fn test_cjk() {
        assert_eq!(normalize_text("日本語"), "日本語");
    }

    #[test]
    fn test_full_pipeline() {
        let input = "<p>Hello &amp; Welcome to <b>DDGS</b>! \x00</p>";
        assert_eq!(normalize_text(input), "Hello & Welcome to DDGS!");
    }
}
