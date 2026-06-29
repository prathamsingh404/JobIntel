from typing import Dict, List
import re
from app.config.settings import settings

class TitleNormalizer:
    """Maps custom job titles to standard canonical roles using config mappings."""

    def __init__(self):
        # Load canonical mappings from settings
        self.mappings: Dict[str, List[str]] = (
            settings.pipeline_config.get("canonical_titles", {})
        )

    def normalize(self, title: str) -> str:
        """Normalizes a raw job title into a canonical slug."""
        if not title:
            return "unknown"
            
        title_lower = title.lower().strip()
        # Clean title of common prefixes/suffixes
        title_clean = re.sub(r"\b(sr|junior|jr|senior|lead|staff|principal|head of|associate|intern)\b", "", title_lower)
        title_clean = re.sub(r"[^a-z\s-]", "", title_clean)
        title_clean = re.sub(r"\s+", " ", title_clean).strip()

        # 1. Look for direct substring matches of configuration aliases
        for canonical, aliases in self.mappings.items():
            for alias in aliases:
                # Use word boundaries for matching to prevent substring errors (e.g. "nlp" in "unpleasant")
                pattern = r"\b" + re.escape(alias.lower()) + r"\b"
                if re.search(pattern, title_lower) or re.search(pattern, title_clean):
                    return canonical

        # 2. Token-based heuristic matching as a fallback
        # Check if key words overlap with canonical mappings
        tokens = set(title_clean.split())
        best_match = None
        max_overlap = 0

        for canonical, aliases in self.mappings.items():
            for alias in aliases:
                alias_tokens = set(alias.lower().split())
                overlap = len(tokens.intersection(alias_tokens))
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_match = canonical

        # If we have at least a 2-word overlap or the alias is a single word and matches
        if best_match and max_overlap >= 1:
            return best_match

        # 3. Default fallback normalization slug
        fallback_slug = re.sub(r"\s+", "_", title_clean)
        fallback_slug = re.sub(r"[^a-z0-9_]", "", fallback_slug)
        return fallback_slug or "other"
