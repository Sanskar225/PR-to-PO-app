import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.domain.repositories.interfaces import IContractRepository
from app.infrastructure.pdf.contract_pdf_parser import PDFContractParser
from app.presentation.api_v1.dependencies import get_contract_repo
from app.core.config import PDF_CONTRACTS_DIR

router = APIRouter(prefix="/contracts", tags=["Contracts Register"])

@router.get("")
async def list_contracts(contract_repo: IContractRepository = Depends(get_contract_repo)):
    contracts = contract_repo.get_all()
    return [
        {
            "contract_id": c.contract_id,
            "supplier_id": c.supplier_id,
            "supplier_name": c.supplier_name,
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat(),
            "value_cap": c.value_cap,
            "consumed_value": c.consumed_value,
            "remaining_headroom": c.remaining_ceiling,
            "rates": c.rates,
            "is_pdf_extracted": c.is_pdf_extracted
        }
        for c in contracts
    ]

@router.post("/upload-pdf")
async def upload_contract_pdf(
    file: UploadFile = File(...),
    contract_repo: IContractRepository = Depends(get_contract_repo)
):
    """
    Task Brief Section 3.8:
    Load the register, and let a buyer add a PDF-only contract (by extracting it from the PDF).
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        PDF_CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
        dest = PDF_CONTRACTS_DIR / file.filename
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extracted = PDFContractParser.parse_pdf(dest)
        if not extracted:
            raise HTTPException(status_code=400, detail="Could not extract contract details from PDF.")

        contract_repo.save(extracted)

        return {
            "status": "success",
            "message": f"Contract {extracted.contract_id} successfully parsed and registered!",
            "contract": {
                "contract_id": extracted.contract_id,
                "supplier_id": extracted.supplier_id,
                "supplier_name": extracted.supplier_name,
                "start_date": extracted.start_date.isoformat(),
                "end_date": extracted.end_date.isoformat(),
                "value_cap": extracted.value_cap,
                "consumed_value": extracted.consumed_value,
                "rates": extracted.rates
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process contract PDF: {str(e)}")
