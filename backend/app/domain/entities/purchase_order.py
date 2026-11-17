from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from app.domain.entities.requirement import RequirementGroup

@dataclass
class ConsolidatedPurchaseOrder:
    po_id: str
    supplier_id: str
    plant: str
    route: str
    first_requirement_created_at: datetime
    requirements: List[RequirementGroup] = field(default_factory=list)

    @property
    def total_value(self) -> float:
        return sum(req.group_value_inr for req in self.requirements)

    def can_consolidate(self, req: RequirementGroup, window_hours: int = 24) -> bool:
        """
        Policy Clause 7.1 Domain Invariant:
        Combine into one PO when they have the same supplier, the same plant,
        and the same route, and were raised within 24 hours of the first requirement
        on that PO (measured from creation time of each requirement's first line).
        """
        if req.decision != "PO":
            return False

        if req.supplier_id != self.supplier_id:
            return False

        if req.plant != self.plant:
            return False

        if req.route != self.route:
            return False

        diff_seconds = (req.first_created_at - self.first_requirement_created_at).total_seconds()
        if diff_seconds < 0:
            return False
        if diff_seconds > (window_hours * 3600):
            return False

        return True

    def add_requirement(self, req: RequirementGroup):
        self.requirements.append(req)
        req.po_id = self.po_id
