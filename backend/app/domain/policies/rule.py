from dataclasses import dataclass
from typing import Optional
from app.domain.policies.specification import Specification

@dataclass
class DomainPolicyRule:
    rule_id: str
    name: str
    clause: str
    specification: Specification
    outcome: str          # PO or SOURCING_REQUEST
    route: str            # CONTRACT_PO, SPOT_PO, RFQ, etc.
    suggest_count: Optional[int] = None
    supplier_selection: Optional[str] = None
    requires_approval: Optional[str] = None
    reason_template: str = ""
