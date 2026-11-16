import io
from fastapi import APIRouter, Query, Response, HTTPException
from typing import Optional, List
from app.services.data_loader import data_loader
from app.services.preferred_suppliers import PreferredSupplierService

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers & Ranking"])
pref_service = PreferredSupplierService(data_loader)

@router.get("/preferred")
async def get_preferred_suppliers(
    date: str = Query("2026-11-01", description="Reference date YYYY-MM-DD"),
    item_code: Optional[str] = Query(None, description="Optional specific item code")
):
    """
    Returns preferred supplier lists as of date.
    If item_code provided, returns ranking for that item.
    Otherwise returns top 3 for all items.
    """
    if item_code:
        if item_code not in data_loader.items:
            raise HTTPException(status_code=404, detail="Item code not found")
        ranked = pref_service.get_preferred_suppliers_for_item(item_code, date)
        return {
            "item_code": item_code,
            "as_of_date": date,
            "ranked_suppliers": ranked
        }

    all_ranked = {}
    for code in sorted(data_loader.items.keys()):
        all_ranked[code] = pref_service.get_preferred_suppliers_for_item(code, date)[:3]

    return {
        "as_of_date": date,
        "items": all_ranked
    }

@router.get("/preferred/export")
async def export_preferred_suppliers_csv(
    date: str = Query("2026-11-01", description="Reference date YYYY-MM-DD")
):
    """
    Task Brief Section 3.5:
    Export it as CSV (item_code, rank, supplier_id, reference_price, top 3) as of a chosen date.
    """
    csv_str = pref_service.export_preferred_suppliers_csv(date, top_k=3)
    filename = f"preferred_suppliers_{date}.csv"
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/list")
async def list_all_suppliers():
    """Lists all suppliers with status, on-time percentage, and ratings."""
    return list(data_loader.suppliers.values())
