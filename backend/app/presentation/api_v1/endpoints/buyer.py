from fastapi import APIRouter, HTTPException, Depends
from app.application.dto.schemas import BuyerOverrideDTO, BuyerApproveDTO
from app.application.use_cases.buyer_actions_use_case import BuyerActionsUseCase
from app.domain.repositories.interfaces import IAuditRepository
from app.presentation.api_v1.dependencies import get_buyer_actions_use_case, get_audit_repo
from app.core.exceptions import DomainException

router = APIRouter(prefix="/buyer", tags=["Buyer Workspace"])

@router.get("/requirements")
async def get_buyer_requirements(use_case: BuyerActionsUseCase = Depends(get_buyer_actions_use_case)):
    return use_case.get_workspace_overview()

@router.post("/approve")
async def approve_requirement(
    req: BuyerApproveDTO,
    use_case: BuyerActionsUseCase = Depends(get_buyer_actions_use_case)
):
    try:
        use_case.approve_requirement(group_id=req.group_id, buyer_name=req.buyer_name)
        return {"status": "success", "message": f"Requirement {req.group_id} approved."}
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/override")
async def override_requirement(
    req: BuyerOverrideDTO,
    use_case: BuyerActionsUseCase = Depends(get_buyer_actions_use_case)
):
    try:
        use_case.override_requirement(
            group_id=req.group_id,
            override_route=req.override_route or "SPOT_PO",
            override_supplier_id=req.override_supplier_id or "",
            comment=req.override_comment,
            buyer_name=req.buyer_name
        )
        return {"status": "success", "message": f"Requirement {req.group_id} overridden."}
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audit-logs")
async def get_audit_logs(audit_repo: IAuditRepository = Depends(get_audit_repo)):
    return audit_repo.get_all_logs()
