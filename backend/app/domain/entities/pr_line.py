from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
from typing import Optional

class UrgencyLevel(str, Enum):
    NORMAL = "Normal"
    EMERGENCY = "Emergency"

    @classmethod
    def from_str(cls, val: str) -> "UrgencyLevel":
        clean = (val or "").strip().lower()
        if clean in ["emergency", "urgent", "critical", "breakdown"]:
            return cls.EMERGENCY
        return cls.NORMAL

@dataclass(frozen=True)
class PurchaseRequisitionLine:
    pr_no: str
    pr_line: int
    created_at: datetime
    requester: str
    department: str
    plant: str
    item_code: Optional[str]
    description: str
    quantity: float
    uom: str
    estimated_unit_price: Optional[float]
    need_by_date: date
    urgency: UrgencyLevel = UrgencyLevel.NORMAL
    resolved_item_code: Optional[str] = None

    @property
    def is_emergency(self) -> bool:
        return self.urgency == UrgencyLevel.EMERGENCY

    @property
    def is_new_item(self) -> bool:
        return self.resolved_item_code == "NEW"
