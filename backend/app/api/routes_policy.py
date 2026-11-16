import io
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.models.schemas import PolicyDocument, PolicyDiff
from app.services.policy_manager import policy_manager

router = APIRouter(prefix="/api/policy", tags=["Policy Management"])

class AmendTextRequest(BaseModel):
    amendment_text: str
    base_version: Optional[str] = None

class ApproveRequest(BaseModel):
    version: str

@router.get("/current")
async def get_current_policy():
    """Returns the currently active policy document."""
    return policy_manager.get_active_policy()

@router.get("/versions")
async def get_all_policy_versions():
    """Returns list of all available policy versions."""
    return {
        "active_version": policy_manager.active_version,
        "available_versions": list(policy_manager.policies.keys())
    }

@router.post("/set-active/{version}")
async def set_active_policy_version(version: str):
    if version not in policy_manager.policies:
        raise HTTPException(status_code=404, detail=f"Policy version {version} not found")
    policy_manager.set_active_version(version)
    return {"status": "success", "active_version": policy_manager.active_version}

@router.post("/amend-text")
async def amend_policy_text(req: AmendTextRequest):
    """
    Parses amendment described in natural language or plain text.
    Produces plain English diff preview.
    """
    diff = policy_manager.parse_amendment_text(req.amendment_text, req.base_version)
    return diff

@router.post("/amend-upload")
async def amend_policy_upload(file: UploadFile = File(...), base_version: Optional[str] = Form(None)):
    """
    Accepts uploaded amendment file (PDF or TXT).
    Extracts text, parses rule changes, and returns diff preview.
    """
    try:
        content = await file.read()
        if file.filename.lower().endswith(".pdf"):
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            extracted_text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    extracted_text += "\n" + t
            diff = policy_manager.parse_amendment_text(extracted_text, base_version)
        else:
            text = content.decode("utf-8", errors="ignore")
            diff = policy_manager.parse_amendment_text(text, base_version)
            
        return diff
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse amendment: {str(e)}")

@router.post("/approve")
async def approve_amendment(req: ApproveRequest):
    """
    Approves a pending amendment and activates the new version.
    """
    doc = policy_manager.approve_amendment(req.version)
    if not doc:
        raise HTTPException(status_code=404, detail=f"No pending amendment found for version {req.version}")
        
    return {
        "status": "success",
        "message": f"Policy version {doc.version} has been approved and is now active!",
        "active_policy": doc
    }
