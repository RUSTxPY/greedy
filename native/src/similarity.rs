/*! Similarity ranking logic
 * 
 * Accelerates search result ranking using Aho-Corasick multi-pattern matching
 * and Rayon for parallel processing.
 */

use aho_corasick::{AhoCorasick, AhoCorasickBuilder};
use regex::Regex;
use once_cell::sync::Lazy;
use rayon::prelude::*;

// Pre-compiled regex for splitting query into tokens
static SPLITTER_RE: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"\W+").expect("valid splitter regex")
});

/// Rank documents based on query tokens.
pub fn rank_similarity(
    query: &str,
    min_token_length: usize,
    titles: &[&str],
    bodies: &[&str],
    hrefs: &[&str],
    out_buckets: &mut [i32],
) {
    let count = titles.len();
    if count == 0 {
        return;
    }

    // 1. Extract and lowercase tokens from query
    let query_lower = query.to_lowercase();
    let tokens: Vec<String> = SPLITTER_RE.split(&query_lower)
        .filter(|s| s.len() >= min_token_length)
        .map(|s| s.to_string())
        .collect();

    // If no tokens to search for, everything is 'neither' unless it's a wiki hit or skipped
    let ac_opt = if tokens.is_empty() {
        None
    } else {
        // Use ASCII case-insensitive if possible, otherwise we still need to lowercase text
        Some(AhoCorasickBuilder::new()
            .ascii_case_insensitive(true)
            .build(&tokens)
            .expect("valid AC matcher"))
    };

    // Use Rayon for parallel processing of documents
    out_buckets.par_iter_mut().enumerate().for_each(|(i, bucket)| {
        let title = titles[i];
        let body = bodies[i];
        let href = hrefs[i];

        // 1. Skip Wikimedia category pages
        if title.contains("Category:") && title.contains("Wikimedia") {
            *bucket = -1;
            return;
        }

        // 2. Wikipedia check
        if href.contains("wikipedia.org") {
            *bucket = 0;
            return;
        }

        // If no tokens, we can't have title/body hits
        let ac = match &ac_opt {
            Some(ac) => ac,
            None => {
                *bucket = 4;
                return;
            }
        };

        // 3. Title / Body match
        // Fast path: if string is ASCII, case-insensitive matcher handles it without allocation
        let hit_title = if title.is_ascii() {
            ac.is_match(title)
        } else {
            ac.is_match(&title.to_lowercase())
        };
        
        let hit_body = if body.is_ascii() {
            ac.is_match(body)
        } else {
            ac.is_match(&body.to_lowercase())
        };

        if hit_title && hit_body {
            *bucket = 1;
        } else if hit_title {
            *bucket = 2;
        } else if hit_body {
            *bucket = 3;
        } else {
            *bucket = 4;
        }
    });
}
