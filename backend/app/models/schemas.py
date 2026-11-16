from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class Item(BaseModel):
    item_code: str
    description: str
    uom: str
    category: str
    item_type: str  # Material, Capex, Service, Consumable, etc.
    standard_price: float

class Supplier(BaseModel):
    supplier_id: str
    name: str
    city: str
    categories: List[str] = []
    status: str  # Active, Blocked, Inactive
    on_time_pct: float
    quality_rating: float

class Plant(BaseModel):
    plant: str
    name: str

class ContractLine(BaseModel):
    contract_id: str
    item_code: str
    description: str
    uom: str
    rate: float

class Contract(BaseModel):
    contract_id: str
    supplier_id: str
    supplier_name: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    value_cap: float
    consumed_value: float = 0.0
    lines: Dict[str, float] = {}  # item_code -> rate
    is_pdf_extracted: bool = False

class POHistoryEntry(BaseModel):
    po_number: str
    po_date: str  # YYYY-MM-DD
    supplier_id: str
    item_code: str
    quantity: float
    uom: str
    unit_price: float
    plant: str
    delivered_on_time: bool

class PRLineInput(BaseModel):
    pr_no: str
    pr_line: int
    created_at: str  # YYYY-MM-DD HH:MM
    requester: str = "Employee"
    department: str = "Operations"
    plant: str
    item_code: Optional[str] = None
    description: str
    quantity: float
    uom: str = "NOS"
    estimated_unit_price: Optional[float] = None
    need_by_date: str  # YYYY-MM-DD
    urgency: str = "Normal"  # Normal, Emergency

class DecisionRecord(BaseModel):
    pr_no: str
    pr_line: int
    resolved_item_code: str
    group_id: str
    po_id: Optional[str] = None
    decision: str  # PO or SOURCING_REQUEST
    route: str     # CONTRACT_PO, EMERGENCY_PO, SPOT_PO, RFQ, RFP, CAPEX_SOURCING, NEW_ITEM_SOURCING, NOT_PROCESSED
    supplier_id: Optional[str] = None
    unit_price: Optional[float] = None
    group_value_inr: float
    suggested_supplier_ids: Optional[str] = None  # Semicolon-separated, e.g. "S014;S013;S016"
    policy_version: str
    reason: str

class PreferredSupplierRecord(BaseModel):
    item_code: str
    rank: int
    supplier_id: str
    supplier_name: Optional[str] = None
    reference_price: float
    po_count_548d: int = 0
    recency_score: float = 0.0
    has_contract: bool = False
    on_time_pct: float = 0.0
    quality_rating: float = 0.0
    composite_score: float = 0.0

class PolicyRule(BaseModel):
    rule_id: str
    name: str
    clause: str
    condition: Dict[str, Any]
    outcome: str
    route: str
    suggest_count: Optional[int] = None
    supplier_selection: Optional[str] = None
    requires_approval: Optional[str] = None

class PolicyDocument(BaseModel):
    policy_id: str = "CORVO-PROC-POL-04"
    version: str = "5.0"
    effective_date: str = "2026-04-01"
    name: str = "Corvo Procurement Policy (PR to PO)"
    owner: str = "Head of Procurement"
    applies_to_plants: List[str] = ["PUN1", "CHK1"]
    clubbing_rules: Dict[str, Any] = {
        "same_item": True,
        "same_plant": True,
        "creation_window_days": 14,
        "need_by_window_days": 7
    }
    history_lookbacks: Dict[str, Any] = {
        "po_history_lookback_days": 365,
        "preferred_supplier_lookback_days": 548
    }
    ranking_weights: Dict[str, float] = {
        "po_count": 3.0,
        "recency": 4.0,
        "contract": 2.0,
        "on_time": 1.5,
        "quality": 1.5
    }
    consolidation_window_hours: int = 24
    rules: List[PolicyRule]

class PolicyDiff(BaseModel):
    base_version: str
    new_version: str
    effective_date: str
    summary_of_changes: List[str]
    rule_changes: List[Dict[str, Any]]
    diff_markdown: str

class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    metadata: Optional[Dict[str, Any]] = None

class BuyerOverrideRequest(BaseModel):
    group_id: str
    override_route: Optional[str] = None
    override_supplier_id: Optional[str] = None
    override_comment: str
    buyer_name: str = "Procurement Buyer"
