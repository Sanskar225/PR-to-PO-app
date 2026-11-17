from datetime import date
from typing import Optional
from fastapi import APIRouter, Query, Response, HTTPException, Depends
from app.application.use_cases.rank_preferred_suppliers_use_case import RankPreferredSuppliersUseCase
from app.domain.repositories.interfaces import ISupplierRepository
from app.presentation.api_v1.dependencies import get_preferred_suppliers_use_case, get_supplier_repo

router = APIRouter(prefix="/suppliers", tags=["Suppliers & Ranking"])

@router.get("/preferred")
async def get_preferred_suppliers(
    date_str: str = Query("2026-11-01", alias="date", description="Reference date YYYY-MM-DD"),
    item_code: Optional[str] = Query(None),
    use_case: RankPreferredSuppliersUseCase = Depends(get_preferred_suppliers_use_case)
):
    try:
        ref_d = date.fromisoformat(date_str[:10])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    rankings = use_case.get_rankings(ref_date=ref_d, item_code=item_code, top_k=3)

    if item_code:
        return {
            "item_code": item_code,
            "as_of_date": date_str,
            "ranked_suppliers": [r.__dict__ for r in rankings.get(item_code, [])]
        }

    return {
        "as_of_date": date_str,
        "items": {code: [s.__dict__ for s in s_list] for code, s_list in rankings.items()}
    }

@router.get("/preferred/export")
async def export_preferred_csv(
    date_str: str = Query("2026-11-01", alias="date"),
    use_case: RankPreferredSuppliersUseCase = Depends(get_preferred_suppliers_use_case)
):
    try:
        ref_d = date.fromisoformat(date_str[:10])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    csv_data = use_case.export_csv(ref_date=ref_d, top_k=3)
    filename = f"preferred_suppliers_{date_str}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/list")
async def list_suppliers(supplier_repo: ISupplierRepository = Depends(get_supplier_repo)):
    return [s.__dict__ for s in supplier_repo.get_all()]
