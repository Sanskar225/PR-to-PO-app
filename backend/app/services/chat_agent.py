import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from app.services.data_loader import data_loader
from app.services.fuzzy_matcher import FuzzyMatcher

class ChatAgent:
    def __init__(self):
        self.matcher = FuzzyMatcher(data_loader.items)

    def parse_user_request(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parses conversational PR intake text into structured fields.
        Context can carry existing state from previous turns in a conversation.
        """
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
            # e.g. 200 nitrile gloves, 50 nos, 100 kg, 250 mtr, 500 ltr
            qty_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(nos|kg|ltr|mtr|pair|box|set|bkt|job)?\b", text_lower)
            if qty_match:
                val = float(qty_match.group(1))
                # avoid capturing year or item code digits if small
                if val != 2026 and val != 1000:
                    state["quantity"] = val
                    if qty_match.group(2):
                        state["uom"] = qty_match.group(2).upper()

        # 4. Need by date detection
        if not state["need_by_date"]:
            # Explicit YYYY-MM-DD
            explicit_date = re.search(r"\b(202[6-9]-[0-1][0-9]-[0-3][0-9])\b", user_text)
            if explicit_date:
                state["need_by_date"] = explicit_date.group(1)
            elif "next friday" in text_lower:
                # Relative date: next Friday
                today = datetime.now()
                days_ahead = 4 - today.weekday() # Friday is 4
                if days_ahead <= 0:
                    days_ahead += 7
                state["need_by_date"] = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            elif "tomorrow" in text_lower:
                state["need_by_date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif "next week" in text_lower:
                state["need_by_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        # 5. Item matching
        if not state["item_code"] or state["item_code"] == "NEW":
            # Strip out recognized quantity, plant, and common PR filler phrases
            cleaned = text_lower
            cleaned = re.sub(r"\b(need|want|buy|order|purchase|for|by|please|send|urgent|urgently|emergency|chk1|pun1|chakan|bhosari)\b", "", cleaned)
            cleaned = re.sub(r"\b\d+(\.\d+)?\s*(nos|kg|ltr|mtr|pair|box|set|bkt|job)?\b", "", cleaned)
            cleaned = re.sub(r"\b(next friday|tomorrow|next week|asap)\b", "", cleaned)
            cleaned = cleaned.strip()

            if cleaned:
                code, score = self.matcher.match(None, cleaned, threshold=65.0)
                if code != "NEW":
                    matched_item = data_loader.items.get(code)
                    state["item_code"] = code
                    state["description"] = matched_item.description
                    state["uom"] = matched_item.uom
                    state["estimated_unit_price"] = matched_item.standard_price
                else:
                    # New or vague item
                    state["item_code"] = "NEW"
                    state["description"] = cleaned.title()

        # Check missing fields
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

        # Generate intelligent assistant response
        if missing:
            if "item description" in missing:
                reply = "What item do you need to procure? Please describe the item or provide its code."
            elif "quantity" in missing:
                reply = f"Got it, for {state['description']} at {state.get('plant', 'the plant')}. How many units do you need?"
            elif "plant" in missing:
                reply = f"Understood, {state['quantity']} {state['uom']} of {state['description']}. Which plant is this for? (PUN1 Bhosari or CHK1 Chakan)"
            elif "need-by date" in missing:
                reply = f"When do you need this delivered by? (e.g. YYYY-MM-DD or 'next Friday')"
            else:
                reply = f"Please provide the missing details: {', '.join(missing)}."
            is_complete = False
        else:
            item_desc = state["description"]
            is_new = (state["item_code"] == "NEW")
            reply = (
                f"**Ready to create Purchase Requisition!**\n\n"
                f"- **Item:** {item_desc} `[{state['item_code']}]` {'*(New Sourcing Item)*' if is_new else ''}\n"
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

chat_agent = ChatAgent()
