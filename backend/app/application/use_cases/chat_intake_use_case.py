import re
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional

from app.domain.repositories.interfaces import IItemRepository
from app.infrastructure.matching.rapidfuzz_matcher import RapidFuzzItemMatcher

class ChatIntakeUseCase:
    def __init__(self, item_repo: IItemRepository):
        self.item_repo = item_repo

    def execute(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        state = context.copy() if context else {
            "item_code": None,
            "description": None,
            "quantity": None,
            "uom": "NOS",
            "plant": None,
            "need_by_date": None,
            "urgency": "Normal",
            "estimated_unit_price": None,
            "missing_fields": []
        }

        text_lower = user_text.lower()

        # 1. Plant detection
        if not state["plant"]:
            if "chakan" in text_lower or "chk1" in text_lower:
                state["plant"] = "CHK1"
            elif "bhosari" in text_lower or "pun1" in text_lower or "pune" in text_lower:
                state["plant"] = "PUN1"

        # 2. Urgency detection
        if any(w in text_lower for w in ["emergency", "critical", "urgent", "breakdown", "asap"]):
            state["urgency"] = "Emergency"

        # 3. Quantity & UOM detection
        if not state["quantity"]:
            qty_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(nos|kg|ltr|mtr|pair|box|set|bkt|job)?\b", text_lower)
            if qty_match:
                val = float(qty_match.group(1))
                if val != 2026 and val != 1000:
                    state["quantity"] = val
                    if qty_match.group(2):
                        state["uom"] = qty_match.group(2).upper()

        # 4. Need by date detection
        if not state["need_by_date"]:
            explicit_date = re.search(r"\b(202[6-9]-[0-1][0-9]-[0-3][0-9])\b", user_text)
            if explicit_date:
                state["need_by_date"] = explicit_date.group(1)
            elif "next friday" in text_lower:
                today = datetime.now()
                days_ahead = 4 - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                state["need_by_date"] = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            elif "tomorrow" in text_lower:
                state["need_by_date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif "next week" in text_lower:
                state["need_by_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        # 5. Item matching via Domain RapidFuzz Adapter
        if not state["item_code"] or state["item_code"] == "NEW":
            cleaned = text_lower
            cleaned = re.sub(r"\b(need|want|buy|order|purchase|for|by|please|send|urgent|urgently|emergency|chk1|pun1|chakan|bhosari)\b", "", cleaned)
            cleaned = re.sub(r"\b\d+(\.\d+)?\s*(nos|kg|ltr|mtr|pair|box|set|bkt|job)?\b", "", cleaned)
            cleaned = re.sub(r"\b(next friday|tomorrow|next week|asap)\b", "", cleaned).strip()

            if cleaned:
                items_map = self.item_repo.get_all_indexed()
                matcher = RapidFuzzItemMatcher(items_map)
                code, score = matcher.resolve_item(None, cleaned, threshold=65.0)
                if code != "NEW":
                    item = items_map.get(code)
                    state["item_code"] = code
                    state["description"] = item.description
                    state["uom"] = item.uom
                    state["estimated_unit_price"] = item.standard_price
                else:
                    state["item_code"] = "NEW"
                    state["description"] = cleaned.title()

        # Missing attributes check
        missing = []
        if not state["item_code"] or not state["description"]:
            missing.append("item description")
        if not state["quantity"]:
            missing.append("quantity")
        if not state["plant"]:
            missing.append("plant (PUN1 Bhosari or CHK1 Chakan)")
        if not state["need_by_date"]:
            missing.append("need-by date")

        state["missing_fields"] = missing

        if missing:
            if "item description" in missing:
                reply = "What item do you need to procure? Please describe the item or provide its code."
            elif "quantity" in missing:
                reply = f"Got it, for {state['description']} at {state.get('plant', 'the plant')}. How many units do you need?"
            elif "plant" in missing:
                reply = f"Understood, {state['quantity']} {state['uom']} of {state['description']}. Which plant is this for? (PUN1 Bhosari or CHK1 Chakan)"
            elif "need-by date" in missing:
                reply = "When do you need this delivered by? (e.g. YYYY-MM-DD or 'next Friday')"
            else:
                reply = f"Please provide the missing details: {', '.join(missing)}."
            is_complete = False
        else:
            is_new = (state["item_code"] == "NEW")
            reply = (
                f"**Ready to create Purchase Requisition!**\n\n"
                f"- **Item:** {state['description']} `[{state['item_code']}]` {'*(New Sourcing Item)*' if is_new else ''}\n"
                f"- **Quantity:** {state['quantity']} {state['uom']}\n"
                f"- **Plant:** {state['plant']}\n"
                f"- **Need-By Date:** {state['need_by_date']}\n"
                f"- **Urgency:** {state['urgency']}\n\n"
                f"Click **Confirm PR** to submit, or let me know if any detail needs adjustment."
            )
            is_complete = True

        return {
            "reply": reply,
            "parsed_pr": state,
            "is_complete": is_complete
        }
