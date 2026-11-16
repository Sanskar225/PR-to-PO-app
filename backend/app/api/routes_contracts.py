import io
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.data_loader import data_loader
from app.services.pdf_contract_extractor import extract_contract_from_pdf
from app.core.config import PDF_CONTRACTS_DIR

router = APIRouter(prefix="/api/contracts", tags=["Contracts"])

@router.get("")
async def list_contracts():
    """Returns all loaded contracts with ceilings, consumed values, and covered items."""
    return list(data_loader.contracts.values())

@router.post("/upload-pdf")
async def upload_contract_pdf(file: UploadFile = File(...)):
    """
    Task Brief Section 3.8:
    Load the register, and let a buyer add a PDF-only contract (by extracting it from the PDF).
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    try:
        PDF_CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
        temp_dest = PDF_CONTRACTS_DIR / file.filename
        with open(temp_dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        contract = extract_contract_from_pdf(temp_dest)
        if not contract:
            raise HTTPException(status_code=400, detail="Could not extract contract details from PDF")
            
        # Add to contracts register
        data_loader.contracts[contract.contract_id] = contract
        
        return {
            "status": "success",
            "message": f"Contract {contract.contract_id} successfully extracted and activated!",
            "contract": contract
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process contract PDF: {str(e)}")
