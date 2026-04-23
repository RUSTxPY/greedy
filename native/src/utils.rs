/*! Utility functions for text processing
 * 
 * Helper functions that may be reused across modules.
 */

/// Check if a string contains HTML tags.
pub fn has_html_tags(text: &str) -> bool {
    text.contains('<') && text.contains('>')
}

/// Check if a string contains HTML entities.
pub fn has_html_entities(text: &str) -> bool {
    text.contains('&') && text.contains(';')
}

/// Fast check if normalization is needed.
/// Returns false only for strings that are definitely already normalized.
pub fn needs_normalization(text: &str) -> bool {
    if text.is_empty() {
        return false;
    }
    
    // Check for HTML
    if has_html_tags(text) || has_html_entities(text) {
        return true;
    }
    
    // Check for leading/trailing whitespace
    if text.starts_with(|c: char| c.is_whitespace()) || 
       text.ends_with(|c: char| c.is_whitespace()) {
        return true;
    }
    
    // Check for multiple consecutive spaces
    if text.contains("  ") {
        return true;
    }
    
    // Check for control characters
    if text.chars().any(|c| c.is_control() && !matches!(c, '\t' | '\n' | '\r')) {
        return true;
    }
    
    // Check for decomposed Unicode (rough check)
    // This is not perfect but catches common cases
    if text.chars().any(|c| (c as u32) > 0x0300 && (c as u32) < 0x036F) {
        // Contains combining characters, needs NFC
        return true;
    }
    
    false
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_has_html_tags() {
        assert!(has_html_tags("<b>test</b>"));
        assert!(has_html_tags("<p>"));
        assert!(!has_html_tags("just text"));
    }

    #[test]
    fn test_has_html_entities() {
        assert!(has_html_entities("&amp;"));
        assert!(has_html_entities("&lt;tag&gt;"));
        assert!(!has_html_entities("just text"));
        assert!(!has_html_entities("& not an entity"));
    }

    #[test]
    fn test_needs_normalization() {
        assert!(!needs_normalization(""));
        assert!(!needs_normalization("clean"));
        assert!(!needs_normalization("hello world"));
        
        assert!(needs_normalization("  spaces  "));
        assert!(needs_normalization("<b>html</b>"));
        assert!(needs_normalization("&amp;"));
        assert!(needs_normalization("two  spaces"));
        assert!(needs_normalization("\x00"));
    }
}
