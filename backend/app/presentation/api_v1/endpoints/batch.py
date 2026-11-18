import io
import csv
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Depends

from app.application.dto.schemas import PRLineDTO, BatchProcessResultDTO, DecisionOutputDTO
from app.application.use_cases.process_batch_use_case import ProcessBatchUseCase
from app.domain.repositories.interfaces import IRequirementRepository
from app.presentation.api_v1.dependencies import get_process_batch_use_case, get_requirement_repo
from app.db.session import get_db
from app.db.models import DecisionModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="", tags=["Batch PR Processing"])

# Cached latest export decisions
_latest_export_cache: List[DecisionOutputDTO] = []

@router.post("/process-batch", response_model=BatchProcessResultDTO)
async def process_batch(
    file: UploadFile = File(...),
    use_case: ProcessBatchUseCase = Depends(get_process_batch_use_case)
):
    """
    Task Brief Section 3.7:
    POST /api/process-batch takes a PR batch CSV and returns the decisions.
    """
    global _latest_export_cache
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))

        # Robust case-insensitive and whitespace-trimmed column mapping
        df.columns = [str(c).strip() for c in df.columns]
        col_map = {c.lower(): c for c in df.columns}
        def get_val(row, *aliases, default=None):
            for a in aliases:
                col = col_map.get(a.lower())
                if col is not None and pd.notna(row.get(col)):
                    return row[col]
            return default

        dtos: List[PRLineDTO] = []
        for idx, row in df.iterrows():
            code_val = get_val(row, "item_code", "item", "material_code")
            if code_val is not None:
                code_val = str(code_val).strip()
                if code_val.lower() in ["", "nan", "none", "null"]:
                    code_val = None

            est_p_raw = get_val(row, "estimated_unit_price", "unit_price", "est_price", "price")
            est_p = None
            if est_p_raw is not None:
                try:
                    est_p = float(est_p_raw)
                except (ValueError, TypeError):
                    est_p = None

            qty_raw = get_val(row, "quantity", "qty", default=1.0)
            try:
                qty = float(qty_raw)
            except (ValueError, TypeError):
                qty = 1.0

            pr_no = str(get_val(row, "pr_no", "pr_number", "pr", default=f"PR-{idx+1:05d}")).strip()
            pr_line_raw = get_val(row, "pr_line", "line", "line_no", default=1)
            try:
                pr_line = int(pr_line_raw)
            except (ValueError, TypeError):
                pr_line = 1

            dtos.append(PRLineDTO(
                pr_no=pr_no,
                pr_line=pr_line,
                created_at=str(get_val(row, "created_at", "pr_date", "date", default="2026-11-01 09:00")).strip(),
                requester=str(get_val(row, "requester", default="Requester")).strip(),
                department=str(get_val(row, "department", default="Operations")).strip(),
                plant=str(get_val(row, "plant", "plant_code", default="PUN1")).strip(),
                item_code=code_val,
                description=str(get_val(row, "description", "item_description", "desc", default="")).strip(),
                quantity=qty,
                uom=str(get_val(row, "uom", "unit", default="NOS")).strip(),
                estimated_unit_price=est_p,
                need_by_date=str(get_val(row, "need_by_date", "need_by", "delivery_date", default="2026-11-15")).strip(),
                urgency=str(get_val(row, "urgency", "priority", default="Normal")).strip()
            ))

        result = use_case.execute(pr_dtos=dtos, filename=file.filename or "batch.csv")
        _latest_export_cache = result.decisions
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch execution failed: {str(e)}")

@router.get("/export-decisions")
async def export_decisions(db: Session = Depends(get_db)):
    """
    Task Brief Section 4: Output format CSV download.
    One row per PR line:
    pr_no,pr_line,resolved_item_code,group_id,po_id,decision,route,supplier_id,unit_price,group_value_inr,suggested_supplier_ids,policy_version,reason
    """
    global _latest_export_cache
    decisions = _latest_export_cache

    if not decisions:
        # Fallback to persistent database if memory cache is empty
        latest_row = db.query(DecisionModel).order_by(DecisionModel.id.desc()).first()
        if latest_row:
            rows = db.query(DecisionModel).filter_by(batch_id=latest_row.batch_id).order_by(DecisionModel.id.asc()).all()
            decisions = [
                DecisionOutputDTO(
                    pr_no=r.pr_no,
                    pr_line=r.pr_line,
                    resolved_item_code=r.resolved_item_code,
                    group_id=r.group_id,
                    po_id=r.po_id,
                    decision=r.decision,
                    route=r.route,
                    supplier_id=r.supplier_id,
                    unit_price=r.unit_price,
                    group_value_inr=r.group_value_inr,
                    suggested_supplier_ids=r.suggested_supplier_ids,
                    policy_version=r.policy_version,
                    reason=r.reason
                )
                for r in rows
            ]

    if not decisions:
        raise HTTPException(status_code=400, detail="No decisions available. Please process a PR batch first.")

    output = io.StringIO()
    writer = csv.writer(output)

    # Mandatory Header (Section 4)
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

    for d in decisions:
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

    version_slug = decisions[0].policy_version.replace(".", "_")
    filename = f"decisions_v{version_slug}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
