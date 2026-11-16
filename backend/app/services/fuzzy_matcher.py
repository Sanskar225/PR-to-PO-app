import re
from typing import Optional, Tuple, Dict
from rapidfuzz import process, fuzz
from app.models.schemas import Item

class FuzzyMatcher:
    def __init__(self, items: Dict[str, Item]):
        self.items = items
        # Normalization map: abbreviation replacements
        self.abbr_map = {
            r"\bbrg\b": "ball bearing",
            r"\bhyd\b": "hydraulic",
            r"\bms\b": "ms",
            r"\bss\b": "ss",
            r"\bgr\b": "grade",
            r"\beot\b": "eot",
        }
        self._build_index()

    def _clean_text(self, text: str) -> str:
        t = text.lower().strip()
        # Remove extra words like 'for maintenance', 'for project'
        t = re.sub(r"\bfor\s+(maintenance|project|plant|repair|urgent|breakdown)\b", "", t)
        for pattern, replacement in self.abbr_map.items():
            t = re.sub(pattern, replacement, t)
        t = re.sub(r"[\s\-_/]+", " ", t).strip()
        return t

    def _build_index(self):
        # We index cleaned description -> item_code
        self.index: Dict[str, str] = {}
        for code, item in self.items.items():
            cleaned = self._clean_text(item.description)
            self.index[cleaned] = code

    def match(self, raw_code: Optional[str], raw_description: str, threshold: float = 75.0) -> Tuple[str, float]:
        """
        Returns (resolved_item_code, match_score).
        If matched, returns (item_code, score).
        If new item, returns ('NEW', 0.0).
        """
        # 1. If explicit item code provided and valid
        if raw_code and str(raw_code).strip() in self.items:
            return str(raw_code).strip(), 100.0

        if not raw_description or not raw_description.strip():
            return "NEW", 0.0

        cleaned_query = self._clean_text(raw_description)

        # 2. Exact match on cleaned
        if cleaned_query in self.index:
            return self.index[cleaned_query], 100.0

        # 3. Fuzzy search using token_sort_ratio and token_set_ratio
        best_match, score, _ = process.extractOne(
            cleaned_query,
            self.index.keys(),
            scorer=fuzz.token_set_ratio
        )

        # Also check with partial ratio for long vs short
        if score < threshold:
            best_match_part, score_part, _ = process.extractOne(
                cleaned_query,
                self.index.keys(),
                scorer=fuzz.token_sort_ratio
            )
            if score_part > score:
                best_match = best_match_part
                score = score_part

        if score >= threshold:
            matched_code = self.index[best_match]
            return matched_code, score

        return "NEW", score
