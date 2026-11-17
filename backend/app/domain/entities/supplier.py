from dataclasses import dataclass, field
from enum import Enum
from typing import List

class SupplierStatus(str, Enum):
    ACTIVE = "Active"
    BLOCKED = "Blocked"
    INACTIVE = "Inactive"

    @classmethod
    def from_str(cls, val: str) -> "SupplierStatus":
        clean = (val or "").strip().lower()
        if clean == "active":
            return cls.ACTIVE
        elif clean == "blocked":
            return cls.BLOCKED
        return cls.INACTIVE

@dataclass(frozen=True)
class Supplier:
    supplier_id: str
    name: str
    city: str
    categories: List[str] = field(default_factory=list)
    status: SupplierStatus = SupplierStatus.ACTIVE
    on_time_pct: float = 0.0
    quality_rating: float = 0.0

    @property
    def is_eligible(self) -> bool:
        """Policy Clause 5.7: Blocked or Inactive suppliers must never receive a PO or be suggested."""
        return self.status == SupplierStatus.ACTIVE

    def serves_category(self, category: str) -> bool:
        if not category:
            return False
        return any(c.lower() == category.lower() for c in self.categories)
