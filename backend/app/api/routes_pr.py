import io
import csv
import uuid
from datetime import datetime
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response, Depends
from sqlalchemy.orm import Session

from app.models.schemas import PRLineInput, DecisionRecord, ChatMessage
from app.services.data_loader import data_loader
from app.services.policy_engine import PolicyEngine
from app.services.policy_manager import policy_manager
from app.services.chat_agent import chat_agent
from app.db.session import get_db
from app.db.models import PRBatchModel, PRLineModel, RequirementGroupModel, DecisionModel

router = APIRouter(prefix="/api", tags=["PR and Decisions"])

# In-memory working cache
latest_batch_decisions: List[DecisionRecord] = []
custom_created_prs: List[PRLineInput] = []

@router.post("/chat")
async def chat_intake(message: ChatMessage):
    """
    Conversational PR intake endpoint.
    """
    res = chat_agent.parse_user_request(message.content, message.metadata)
    return res

@router.post("/pr/submit")
async def submit_chat_pr(pr_data: PRLineInput, db: Session = Depends(get_db)):
    """
    Submits a PR created via conversational chat intake, persists it to DB,
    and evaluates it immediately.
    """
    if not pr_data.pr_no:
        pr_data.pr_no = f"PR-CHAT-{len(custom_created_prs) + 1:04d}"
    if not pr_data.created_at:
        pr_data.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        
    custom_created_prs.append(pr_data)
    
    # Save to SQLite
    pr_row = PRLineModel(
        batch_id="CHAT_INTAKE",
        pr_no=pr_data.pr_no,
        pr_line=pr_data.pr_line,
        created_at=pr_data.created_at,
        requester=pr_data.requester,
        department=pr_data.department,
        plant=pr_data.plant,
        item_code=pr_data.item_code,
        description=pr_data.description,
        quantity=pr_data.quantity,
        uom=pr_data.uom,
        estimated_unit_price=pr_data.estimated_unit_price,
        need_by_date=pr_data.need_by_date,
        urgency=pr_data.urgency
    )
    db.add(pr_row)
    db.commit()
    
    # Evaluate decision using active policy
    policy = policy_manager.get_active_policy()
    engine = PolicyEngine(data_loader, policy)
    decision = engine.process_pr_batch([pr_data])[0]
    
    # Save decision & requirement to DB
    dec_row = DecisionModel(
        batch_id="CHAT_INTAKE",
        pr_no=decision.pr_no,
        pr_line=decision.pr_line,
        resolved_item_code=decision.resolved_item_code,
        group_id=decision.group_id,
        po_id=decision.po_id,
        decision=decision.decision,
        route=decision.route,
        supplier_id=decision.supplier_id,
        unit_price=decision.unit_price,
        group_value_inr=decision.group_value_inr,
        suggested_supplier_ids=decision.suggested_supplier_ids,
        policy_version=decision.policy_version,
        reason=decision.reason
    )
    db.add(dec_row)
    db.commit()
    
    latest_batch_decisions.append(decision)
    
    return {
        "status": "success",
        "pr": pr_data,
        "decision": decision
    }

@router.post("/process-batch")
async def process_batch(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Core Batch Processing API required by Task Brief Section 3.7.
    Accepts a PR batch CSV, executes the decision engine, and persists batch and decisions in SQLite.
    """
    global latest_batch_decisions
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        batch_id = f"BATCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        policy = policy_manager.get_active_policy()
        
        pr_lines: List[PRLineInput] = []
        for _, row in df.iterrows():
            item_code_val = str(row["item_code"]).strip() if pd.notna(row.get("item_code")) else None
            if item_code_val == "" or item_code_val == "nan":
                item_code_val = None
                
            est_price = float(row["estimated_unit_price"]) if pd.notna(row.get("estimated_unit_price")) else None
            
            pr_lines.append(PRLineInput(
                pr_no=str(row["pr_no"]).strip(),
                pr_line=int(row["pr_line"]),
                created_at=str(row["created_at"]).strip(),
                requester=str(row.get("requester", "Requester")).strip(),
                department=str(row.get("department", "Stores")).strip(),
                plant=str(row["plant"]).strip(),
                item_code=item_code_val,
                description=str(row["description"]).strip(),
                quantity=float(row["quantity"]),
                uom=str(row.get("uom", "NOS")).strip(),
                estimated_unit_price=est_price,
                need_by_date=str(row["need_by_date"]).strip(),
                urgency=str(row.get("urgency", "Normal")).strip()
            ))
            
        engine = PolicyEngine(data_loader, policy)
        decisions = engine.process_pr_batch(pr_lines)
        
        # Persist Batch Record
        batch_record = PRBatchModel(
            batch_id=batch_id,
            filename=file.filename or "batch.csv",
            total_lines=len(decisions),
            policy_version_applied=policy.version
        )
        db.add(batch_record)
        
        # Bulk save decisions & requirement groups
        created_groups = {}
        for d in decisions:
            if d.group_id not in created_groups:
                req_model = RequirementGroupModel(
                    group_id=d.group_id,
                    batch_id=batch_id,
                    plant=d.group_id, # will match PR plant
                    resolved_item_code=d.resolved_item_code,
                    total_quantity=0.0,
                    uom="NOS",
                    group_value_inr=d.group_value_inr,
                    decision=d.decision,
                    route=d.route,
                    po_id=d.po_id,
                    supplier_id=d.supplier_id,
                    unit_price=d.unit_price,
                    suggested_supplier_ids=d.suggested_supplier_ids,
                    policy_version=d.policy_version,
                    reason=d.reason,
                    status="APPROVED" if d.po_id else "PENDING_SOURCING"
                )
                db.add(req_model)
                created_groups[d.group_id] = req_model
                
            db.add(DecisionModel(
                batch_id=batch_id,
                pr_no=d.pr_no,
                pr_line=d.pr_line,
                resolved_item_code=d.resolved_item_code,
                group_id=d.group_id,
                po_id=d.po_id,
                decision=d.decision,
                route=d.route,
                supplier_id=d.supplier_id,
                unit_price=d.unit_price,
                group_value_inr=d.group_value_inr,
                suggested_supplier_ids=d.suggested_supplier_ids,
                policy_version=d.policy_version,
                reason=d.reason
            ))
            
        db.commit()
        
        latest_batch_decisions.clear()
        latest_batch_decisions.extend(decisions)
        
        # Summary statistics
        route_counts = {}
        total_val = 0.0
        po_count = len(set(d.po_id for d in decisions if d.po_id))
        group_count = len(set(d.group_id for d in decisions))
        
        for d in decisions:
            route_counts[d.route] = route_counts.get(d.route, 0) + 1
            total_val += d.group_value_inr
            
        return {
            "status": "success",
            "batch_id": batch_id,
            "total_lines": len(decisions),
            "unique_requirements": group_count,
            "consolidated_pos": po_count,
            "total_value_inr": round(total_val, 2),
            "route_distribution": route_counts,
            "policy_version_applied": policy.version,
            "decisions": decisions
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to process batch: {str(e)}")

@router.get("/export-decisions")
async def export_decisions(version: Optional[str] = None):
    """
    Task Brief Section 4: Output format CSV download.
    pr_no,pr_line,resolved_item_code,group_id,po_id,decision,route,supplier_id,unit_price,group_value_inr,suggested_supplier_ids,policy_version,reason
    """
    global latest_batch_decisions
    if not latest_batch_decisions:
        raise HTTPException(status_code=400, detail="No decisions available. Please process a batch first.")
        
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "pr_no",
        "pr_line",
        "resolved_item_code",
        "group_id",
        "po_id",
        "decision",
        "route",
        "supplier_id",
        "unit_price",
        "group_value_inr",
        "suggested_supplier_ids",
        "policy_version",
        "reason"
    ])
    
    for d in latest_batch_decisions:
        writer.writerow([
            d.pr_no,
            d.pr_line,
            d.resolved_item_code,
            d.group_id,
            d.po_id or "",
            d.decision,
            d.route,
            d.supplier_id or "",
            d.unit_price if d.unit_price is not None else "",
            d.group_value_inr,
            d.suggested_supplier_ids or "",
            d.policy_version,
            d.reason
        ])
        
    output.seek(0)
    filename = f"decisions_v{latest_batch_decisions[0].policy_version.replace('.', '_')}.csv"
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
