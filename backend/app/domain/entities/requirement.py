from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Optional
from app.domain.entities.pr_line import PurchaseRequisitionLine

@dataclass
class RequirementGroup:
    group_id: str
    resolved_item_code: str
    plant: str
    first_pr: PurchaseRequisitionLine
    lines: List[PurchaseRequisitionLine] = field(default_factory=list)
    
    # Decision outcomes set during evaluation
    decision: Optional[str] = None  # PO or SOURCING_REQUEST
    route: Optional[str] = None     # CONTRACT_PO, SPOT_PO, etc.
    po_id: Optional[str] = None
    supplier_id: Optional[str] = None
    unit_price: Optional[float] = None
    group_value_inr: float = 0.0
    suggested_supplier_ids: Optional[str] = None
    policy_version: str = "5.0"
    reason: str = ""
    status: str = "PENDING"

    def __post_init__(self):
        if not self.lines:
            self.lines = [self.first_pr]

    @property
    def requirement_date(self) -> date:
        """Policy Clause 2.3: The requirement date is the creation date of its first line."""
        return self.first_pr.created_at.date()

    @property
    def first_created_at(self) -> datetime:
        return self.first_pr.created_at

    @property
    def first_need_by_date(self) -> date:
        return self.first_pr.need_by_date

    @property
    def total_quantity(self) -> float:
        return sum(line.quantity for line in self.lines)

    @property
    def is_emergency(self) -> bool:
        """Policy Clause 2.3: If any line in the requirement is marked Emergency, requirement is an emergency."""
        return any(line.is_emergency for line in self.lines)

    def can_absorb(
        self,
        candidate: PurchaseRequisitionLine,
        creation_window_days: int = 14,
        need_by_window_days: int = 7
    ) -> bool:
        """
        Policy Clause 2.2 Domain Invariant:
        A line joins an existing requirement when it is for the same item,
        for the same plant, was created within 14 calendar days of the requirement's
        first line, and its need-by date is within 7 days (either side) of the
        first line's need-by date.
        Clause 1.2: A new item is never clubbed with other lines.
        """
        if candidate.is_new_item or self.resolved_item_code == "NEW":
            return False

        if candidate.resolved_item_code != self.resolved_item_code:
            return False

        if candidate.plant != self.plant:
            return False

        # Created within 14 calendar days of first line
        time_diff = candidate.created_at - self.first_created_at
        if time_diff.total_seconds() < 0:
            return False
        if time_diff.total_seconds() > (creation_window_days * 86400):
            return False

        # Need-by date within 7 days (either side)
        day_diff = abs((candidate.need_by_date - self.first_need_by_date).days)
        if day_diff > need_by_window_days:
            return False

        return True

    def add_line(self, line: PurchaseRequisitionLine):
        self.lines.append(line)
