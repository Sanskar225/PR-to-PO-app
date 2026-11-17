from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.db.session import Base

class ItemModel(Base):
    __tablename__ = "items"
    
    item_code = Column(String(50), primary_key=True, index=True)
    description = Column(String(255), nullable=False, index=True)
    uom = Column(String(20), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    item_type = Column(String(50), nullable=False)  # Material, Capex, Service, etc.
    standard_price = Column(Float, nullable=False)

class SupplierModel(Base):
    __tablename__ = "suppliers"
    
    supplier_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=True)
    categories = Column(Text, nullable=True)  # Semicolon-separated or JSON
    status = Column(String(50), nullable=False, index=True)  # Active, Blocked, Inactive
    on_time_pct = Column(Float, default=0.0)
    quality_rating = Column(Float, default=0.0)

class PlantModel(Base):
    __tablename__ = "plants"
    
    plant = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)

class ContractModel(Base):
    __tablename__ = "contracts"
    
    contract_id = Column(String(50), primary_key=True, index=True)
    supplier_id = Column(String(50), ForeignKey("suppliers.supplier_id"), nullable=False)
    supplier_name = Column(String(255), nullable=False)
    start_date = Column(String(20), nullable=False, index=True)
    end_date = Column(String(20), nullable=False, index=True)
    value_cap = Column(Float, nullable=False)
    consumed_value = Column(Float, default=0.0)
    is_pdf_extracted = Column(Boolean, default=False)
    
    lines = relationship("ContractLineModel", back_populates="contract", cascade="all, delete-orphan")

class ContractLineModel(Base):
    __tablename__ = "contract_lines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(50), ForeignKey("contracts.contract_id"), nullable=False, index=True)
    item_code = Column(String(50), ForeignKey("items.item_code"), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    uom = Column(String(20), nullable=True)
    rate = Column(Float, nullable=False)
    
    contract = relationship("ContractModel", back_populates="lines")

class POHistoryModel(Base):
    __tablename__ = "po_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    po_number = Column(String(50), nullable=False, index=True)
    po_date = Column(String(20), nullable=False, index=True)
    supplier_id = Column(String(50), ForeignKey("suppliers.supplier_id"), nullable=False, index=True)
    item_code = Column(String(50), ForeignKey("items.item_code"), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    uom = Column(String(20), default="NOS")
    unit_price = Column(Float, nullable=False)
    plant = Column(String(50), nullable=False, index=True)
    delivered_on_time = Column(Boolean, default=True)

class PRBatchModel(Base):
    __tablename__ = "pr_batches"
    
    batch_id = Column(String(50), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    total_lines = Column(Integer, default=0)
    policy_version_applied = Column(String(50), nullable=False)

class PRLineModel(Base):
    __tablename__ = "pr_lines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(50), ForeignKey("pr_batches.batch_id"), nullable=True, index=True)
    pr_no = Column(String(50), nullable=False, index=True)
    pr_line = Column(Integer, nullable=False)
    created_at = Column(String(50), nullable=False, index=True)
    requester = Column(String(100), default="Employee")
    department = Column(String(100), default="Operations")
    plant = Column(String(50), nullable=False, index=True)
    item_code = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False)
    uom = Column(String(20), default="NOS")
    estimated_unit_price = Column(Float, nullable=True)
    need_by_date = Column(String(20), nullable=False)
    urgency = Column(String(20), default="Normal")

class RequirementGroupModel(Base):
    __tablename__ = "requirements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(50), nullable=False, index=True)
    batch_id = Column(String(50), nullable=True, index=True)
    plant = Column(String(50), nullable=False)
    resolved_item_code = Column(String(50), nullable=False)
    total_quantity = Column(Float, nullable=False)
    uom = Column(String(20), default="NOS")
    group_value_inr = Column(Float, nullable=False)
    decision = Column(String(50), nullable=False) # PO or SOURCING_REQUEST
    route = Column(String(50), nullable=False)    # CONTRACT_PO, SPOT_PO, etc.
    po_id = Column(String(50), nullable=True, index=True)
    supplier_id = Column(String(50), nullable=True)
    unit_price = Column(Float, nullable=True)
    suggested_supplier_ids = Column(Text, nullable=True)
    policy_version = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING") # PENDING, APPROVED, OVERRIDDEN
    created_at = Column(DateTime, default=datetime.utcnow)

class DecisionModel(Base):
    __tablename__ = "decisions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(50), nullable=True, index=True)
    pr_no = Column(String(50), nullable=False, index=True)
    pr_line = Column(Integer, nullable=False)
    resolved_item_code = Column(String(50), nullable=False)
    group_id = Column(String(50), nullable=False, index=True)
    po_id = Column(String(50), nullable=True, index=True)
    decision = Column(String(50), nullable=False)
    route = Column(String(50), nullable=False)
    supplier_id = Column(String(50), nullable=True)
    unit_price = Column(Float, nullable=True)
    group_value_inr = Column(Float, nullable=False)
    suggested_supplier_ids = Column(Text, nullable=True)
    policy_version = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PolicyVersionModel(Base):
    __tablename__ = "policy_versions"
    
    version = Column(String(50), primary_key=True, index=True)
    policy_id = Column(String(100), default="CORVO-PROC-POL-04")
    name = Column(String(255), default="Corvo Procurement Policy")
    effective_date = Column(String(20), nullable=False)
    owner = Column(String(100), default="Head of Procurement")
    rules_json = Column(Text, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    group_id = Column(String(50), nullable=True, index=True)
    actor = Column(String(100), default="Procurement Buyer")
    action = Column(String(50), nullable=False)  # APPROVE, OVERRIDE, POLICY_UPDATE
    details = Column(Text, nullable=True)
    override_route = Column(String(50), nullable=True)
    override_supplier_id = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)
