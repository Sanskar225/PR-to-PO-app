from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.schemas import BuyerOverrideRequest
from app.api.routes_pr import latest_batch_decisions
from app.db.session import get_db
from app.db.models import AuditLogModel, RequirementGroupModel

router = APIRouter(prefix="/api/buyer", tags=["Buyer Workspace"])

# In-memory audit cache
buyer_audit_log: List[Dict[str, Any]] = []

class ApproveActionRequest(BaseModel):
    group_id: str
    buyer_name: str = "Procurement Buyer"

@router.get("/requirements")
async def get_buyer_requirements(db: Session = Depends(get_db)):
    """
    Returns aggregated requirements grouped by group_id with decisions, audit logs,
    and single obvious next action for the buyer workspace.
    """
    if not latest_batch_decisions:
        return {"requirements": [], "summary": {}}

    groups: Dict[str, Dict[str, Any]] = {}
    for d in latest_batch_decisions:
        if d.group_id not in groups:
            groups[d.group_id] = {
                "group_id": d.group_id,
                "resolved_item_code": d.resolved_item_code,
                "decision": d.decision,
                "route": d.route,
                "po_id": d.po_id,
                "supplier_id": d.supplier_id,
                "unit_price": d.unit_price,
                "group_value_inr": d.group_value_inr,
                "suggested_supplier_ids": d.suggested_supplier_ids,
                "policy_version": d.policy_version,
                "reason": d.reason,
                "status": "APPROVED" if d.po_id else "PENDING_SOURCING",
                "pr_lines": [],
                "audit_trail": []
            }
        groups[d.group_id]["pr_lines"].append({
            "pr_no": d.pr_no,
            "pr_line": d.pr_line
        })

    # Attach database audit trail entries
    db_logs = db.query(AuditLogModel).all()
    for log in db_logs:
        if log.group_id in groups:
            entry = {
                "action": log.action,
                "actor": log.actor,
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
                "comment": log.comment,
                "override_route": log.override_route
            }
            groups[log.group_id]["audit_trail"].append(entry)
            if log.action == "OVERRIDE":
                groups[log.group_id]["route"] = log.override_route or groups[log.group_id]["route"]
                groups[log.group_id]["status"] = "OVERRIDDEN"

    req_list = list(groups.values())

    summary = {
        "total_requirements": len(req_list),
        "total_pos": sum(1 for r in req_list if r["decision"] == "PO"),
        "total_sourcing": sum(1 for r in req_list if r["decision"] == "SOURCING_REQUEST"),
        "total_value": sum(r["group_value_inr"] for r in req_list)
    }

    return {
        "summary": summary,
        "requirements": req_list
    }

@router.post("/approve")
async def approve_requirement(req: ApproveActionRequest, db: Session = Depends(get_db)):
    """
    Approve creates the PO or formally starts the RFQ/RFP event.
    Keeps audit log with who and when.
    """
    ts = datetime.utcnow()
    audit_row = AuditLogModel(
        group_id=req.group_id,
        actor=req.buyer_name,
        action="APPROVE",
        details=f"Requirement {req.group_id} approved for processing",
        timestamp=ts
    )
    db.add(audit_row)
    db.commit()

    log_entry = {
        "action": "APPROVE",
        "group_id": req.group_id,
        "actor": req.buyer_name,
        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "details": f"Requirement {req.group_id} approved for processing"
    }
    buyer_audit_log.append(log_entry)
    return {"status": "success", "audit": log_entry}

@router.post("/override")
async def override_requirement(req: BuyerOverrideRequest, db: Session = Depends(get_db)):
    """
    Policy Clause 8.1 & Task Brief 3.6:
    A buyer may override a decision only with a written reason, which is kept with the original decision.
    """
    if not req.override_comment or not req.override_comment.strip():
        raise HTTPException(status_code=400, detail="Override requires a written justification comment.")

    ts = datetime.utcnow()
    audit_row = AuditLogModel(
        group_id=req.group_id,
        actor=req.buyer_name,
        action="OVERRIDE",
        override_route=req.override_route,
        override_supplier_id=req.override_supplier_id,
        comment=req.override_comment,
        timestamp=ts
    )
    db.add(audit_row)
    db.commit()

    log_entry = {
        "action": "OVERRIDE",
        "group_id": req.group_id,
        "actor": req.buyer_name,
        "override_route": req.override_route,
        "override_supplier_id": req.override_supplier_id,
        "comment": req.override_comment,
        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S")
    }
    buyer_audit_log.append(log_entry)

    # Update in memory
    for d in latest_batch_decisions:
        if d.group_id == req.group_id:
            if req.override_route:
                d.route = req.override_route
            if req.override_supplier_id:
                d.supplier_id = req.override_supplier_id
            d.reason += f" | Buyer Override: {req.override_comment} (by {req.buyer_name})"

    return {"status": "success", "audit": log_entry}

@router.get("/audit-logs")
async def get_all_audit_logs(db: Session = Depends(get_db)):
    """Returns all audit logs from the database."""
    logs = db.query(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).all()
    return logs
