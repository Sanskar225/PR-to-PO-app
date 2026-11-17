from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PRLineDTO(BaseModel):
    pr_no: str
    pr_line: int
    created_at: str
    requester: str = "Employee"
    department: str = "Operations"
    plant: str
    item_code: Optional[str] = None
    description: str
    quantity: float
    uom: str = "NOS"
    estimated_unit_price: Optional[float] = None
    need_by_date: str
    urgency: str = "Normal"

class DecisionOutputDTO(BaseModel):
    pr_no: str
    pr_line: int
    resolved_item_code: str
    group_id: str
    po_id: Optional[str] = None
    decision: str  # PO or SOURCING_REQUEST
    route: str     # CONTRACT_PO, SPOT_PO, RFQ, RFP, CAPEX_SOURCING, etc.
    supplier_id: Optional[str] = None
    unit_price: Optional[float] = None
    group_value_inr: float
    suggested_supplier_ids: Optional[str] = None
    policy_version: str
    reason: str

class BatchProcessResultDTO(BaseModel):
    batch_id: str
    filename: str
    total_lines: int
    unique_requirements: int
    consolidated_pos: int
    total_value_inr: float
    route_distribution: Dict[str, int]
    policy_version_applied: str
    decisions: List[DecisionOutputDTO]

class PolicyDiffDTO(BaseModel):
    base_version: str
    new_version: str
    effective_date: str
    summary_of_changes: List[str]
    rule_changes: List[Dict[str, Any]]
    diff_markdown: str

class ChatMessageDTO(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class BuyerOverrideDTO(BaseModel):
    group_id: str
    override_route: Optional[str] = None
    override_supplier_id: Optional[str] = None
    override_comment: str
    buyer_name: str = "Procurement Buyer"

class BuyerApproveDTO(BaseModel):
    group_id: str
    buyer_name: str = "Procurement Buyer"
