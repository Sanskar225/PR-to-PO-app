import io
import csv
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Depends

from app.application.dto.schemas import PRLineDTO, BatchProcessResultDTO, DecisionOutputDTO
from app.application.use_cases.process_batch_use_case import ProcessBatchUseCase
from app.domain.repositories.interfaces import IRequirementRepository
from app.presentation.api_v1.dependencies import get_process_batch_use_case, get_requirement_repo

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

        dtos: List[PRLineDTO] = []
        for _, row in df.iterrows():
            code_val = str(row["item_code"]).strip() if pd.notna(row.get("item_code")) else None
            if code_val in ["", "nan", "None"]:
                code_val = None
            est_p = float(row["estimated_unit_price"]) if pd.notna(row.get("estimated_unit_price")) else None

            dtos.append(PRLineDTO(
                pr_no=str(row["pr_no"]).strip(),
                pr_line=int(row["pr_line"]),
                created_at=str(row["created_at"]).strip(),
                requester=str(row.get("requester", "Requester")).strip(),
                department=str(row.get("department", "Operations")).strip(),
                plant=str(row["plant"]).strip(),
                item_code=code_val,
                description=str(row["description"]).strip(),
                quantity=float(row["quantity"]),
                uom=str(row.get("uom", "NOS")).strip(),
                estimated_unit_price=est_p,
                need_by_date=str(row["need_by_date"]).strip(),
                urgency=str(row.get("urgency", "Normal")).strip()
            ))

        result = use_case.execute(pr_dtos=dtos, filename=file.filename or "batch.csv")
        _latest_export_cache = result.decisions
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch execution failed: {str(e)}")

@router.get("/export-decisions")
async def export_decisions():
    """
    Task Brief Section 4: Output format CSV download.
    One row per PR line:
    pr_no,pr_line,resolved_item_code,group_id,po_id,decision,route,supplier_id,unit_price,group_value_inr,suggested_supplier_ids,policy_version,reason
    """
    global _latest_export_cache
    if not _latest_export_cache:
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

    for d in _latest_export_cache:
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

    version_slug = _latest_export_cache[0].policy_version.replace(".", "_")
    filename = f"decisions_v{version_slug}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
