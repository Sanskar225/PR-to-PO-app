import io
from typing import Optional
import pypdf
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel

from app.application.dto.schemas import PolicyDiffDTO
from app.application.use_cases.apply_policy_amendment_use_case import ApplyPolicyAmendmentUseCase
from app.domain.repositories.interfaces import IPolicyRepository
from app.presentation.api_v1.dependencies import get_apply_amendment_use_case, get_policy_repo

router = APIRouter(prefix="/policy", tags=["Policy Management"])

class AmendTextReq(BaseModel):
    amendment_text: str
    base_version: Optional[str] = None

class ApproveReq(BaseModel):
    version: str

@router.get("/current")
async def get_current_policy(policy_repo: IPolicyRepository = Depends(get_policy_repo)):
    active = policy_repo.get_active_policy()
    return active.raw_data

@router.get("/versions")
async def get_policy_versions(policy_repo: IPolicyRepository = Depends(get_policy_repo)):
    active = policy_repo.get_active_policy()
    return {
        "active_version": active.version,
        "available_versions": policy_repo.get_all_versions()
    }

@router.post("/set-active/{version}")
async def set_active_policy(version: str, policy_repo: IPolicyRepository = Depends(get_policy_repo)):
    target = policy_repo.get_by_version(version)
    if not target:
        raise HTTPException(status_code=404, detail=f"Policy version {version} not found.")
    policy_repo.set_active_version(version)
    return {"status": "success", "active_version": version}

@router.post("/amend-text", response_model=PolicyDiffDTO)
async def amend_policy_text(
    req: AmendTextReq,
    use_case: ApplyPolicyAmendmentUseCase = Depends(get_apply_amendment_use_case)
):
    return use_case.parse_amendment(req.amendment_text, req.base_version)

@router.post("/amend-upload", response_model=PolicyDiffDTO)
async def amend_policy_upload(
    file: UploadFile = File(...),
    base_version: Optional[str] = Form(None),
    use_case: ApplyPolicyAmendmentUseCase = Depends(get_apply_amendment_use_case)
):
    try:
        content = await file.read()
        if file.filename.lower().endswith(".pdf"):
            reader = pypdf.PdfReader(io.BytesIO(content))
            full_text = ""
            for p in reader.pages:
                t = p.extract_text()
                if t:
                    full_text += "\n" + t
            return use_case.parse_amendment(full_text, base_version)
        else:
            text = content.decode("utf-8", errors="ignore")
            return use_case.parse_amendment(text, base_version)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse amendment document: {str(e)}")

@router.post("/approve")
async def approve_amendment(
    req: ApproveReq,
    use_case: ApplyPolicyAmendmentUseCase = Depends(get_apply_amendment_use_case)
):
    try:
        activated = use_case.approve_amendment(req.version)
        return {
            "status": "success",
            "message": f"Policy version {activated.version} has been approved and activated!",
            "active_policy": activated.raw_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
