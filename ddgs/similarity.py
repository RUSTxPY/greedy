"""Simple filter ranker."""

import re
from typing import Final


class SimpleFilterRanker:
    """Simple filter ranker.

    1) Pull any doc with 'wikipedia.org' in its href to the top.
    2) Bucket the rest according to where query tokens appear:
       - both title & body/description
       - title only
       - body only
       - neither
    3) Return wikipedia-top + both + title-only + body-only + neither.
    """

    _splitter: Final = re.compile(r"\W+")

    def __init__(self, min_token_length: int = 3) -> None:
        self.min_token_length = min_token_length

    def _extract_tokens(self, query: str) -> set[str]:
        """Split on non-word characters & filter out short tokens."""
        return {token for token in self._splitter.split(query.lower()) if len(token) >= self.min_token_length}

    def _has_any_token(self, text: str, tokens: set[str]) -> bool:
        """Check if any token is a substring of the lower-cased text."""
        lower_text = text.lower()
        return any(tok in lower_text for tok in tokens)

    def rank(self, docs: list[dict[str, str]], query: str) -> list[dict[str, str]]:
        """Rank a list of docs based on a query string."""
        if not docs:
            return []

        # Try native ranking first
        try:
            from .utils_native import is_native_available, rank_similarity_native
            if is_native_available():
                titles = [doc.get("title", "") for doc in docs]
                bodies = [doc.get("body", doc.get("description", "")) for doc in docs]
                hrefs = [doc.get("href", "") for doc in docs]
                
                bucket_indices = rank_similarity_native(
                    query, 
                    self.min_token_length, 
                    titles, 
                    bodies, 
                    hrefs
                )
                
                # Reconstruct buckets
                wiki_hits = []
                both = []
                title_only = []
                body_only = []
                neither = []
                
                for i, bucket_idx in enumerate(bucket_indices):
                    doc = docs[i]
                    if bucket_idx == 0:
                        wiki_hits.append(doc)
                    elif bucket_idx == 1:
                        both.append(doc)
                    elif bucket_idx == 2:
                        title_only.append(doc)
                    elif bucket_idx == 3:
                        body_only.append(doc)
                    elif bucket_idx == 4:
                        neither.append(doc)
                    # -1 (skip) is ignored, as in original Python
                
                return wiki_hits + both + title_only + body_only + neither
        except Exception:
            # Fall back to pure Python
            pass

        # Pure Python fallback
        tokens = self._extract_tokens(query)

        wiki_hits = []
        both = []
        title_only = []
        body_only = []
        neither = []

        for doc in docs:
            href = doc.get("href", "")
            title = doc.get("title", "")
            body = doc.get("body", doc.get("description", ""))

            if all(x in title for x in ["Category:", "Wikimedia"]):
                continue

            if "wikipedia.org" in href:
                wiki_hits.append(doc)
                continue

            hit_title = self._has_any_token(title, tokens)
            hit_body = self._has_any_token(body, tokens)

            if hit_title and hit_body:
                both.append(doc)
            elif hit_title:
                title_only.append(doc)
            elif hit_body:
                body_only.append(doc)
            else:
                neither.append(doc)

        return wiki_hits + both + title_only + body_only + neither
