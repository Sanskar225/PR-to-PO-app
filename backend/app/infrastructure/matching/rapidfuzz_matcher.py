import re
from typing import Dict, Optional, Tuple
from rapidfuzz import process, fuzz
from app.domain.entities.item import Item

class RapidFuzzItemMatcher:
    def __init__(self, items: Dict[str, Item]):
        self.items = items
        self.abbr_map = {
            r"\bbrg\b": "ball bearing",
            r"\bhyd\b": "hydraulic",
            r"\bms\b": "ms",
            r"\bss\b": "ss",
            r"\bgr\b": "grade",
            r"\beot\b": "eot",
        }
        self._build_index()

    def _normalize(self, text: str) -> str:
        t = (text or "").lower().strip()
        t = re.sub(r"\bfor\s+(maintenance|project|plant|repair|urgent|breakdown)\b", "", t)
        for pat, rep in self.abbr_map.items():
            t = re.sub(pat, rep, t)
        t = re.sub(r"[\s\-_/]+", " ", t).strip()
        return t

    def _build_index(self):
        self.desc_to_code: Dict[str, str] = {}
        for code, item in self.items.items():
            cleaned = self._normalize(item.description)
            self.desc_to_code[cleaned] = code

    def resolve_item(
        self,
        raw_code: Optional[str],
        raw_description: str,
        threshold: float = 75.0
    ) -> Tuple[str, float]:
        """
        Policy Clause 1.1: If requester gave an item code, use it. If not, match description.
        Policy Clause 1.2: A line matching no item is a NEW item.
        """
        if raw_code and str(raw_code).strip() in self.items:
            return str(raw_code).strip(), 100.0

        if not raw_description or not raw_description.strip():
            return "NEW", 0.0

        cleaned = self._normalize(raw_description)
        if cleaned in self.desc_to_code:
            return self.desc_to_code[cleaned], 100.0

        # RapidFuzz match
        best_match, score, _ = process.extractOne(
            cleaned,
            self.desc_to_code.keys(),
            scorer=fuzz.token_set_ratio
        )

        if score < threshold:
            best_part, score_part, _ = process.extractOne(
                cleaned,
                self.desc_to_code.keys(),
                scorer=fuzz.token_sort_ratio
            )
            if score_part > score:
                best_match = best_part
                score = score_part

        if score >= threshold:
            return self.desc_to_code[best_match], score

        return "NEW", score
