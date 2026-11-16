import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.data_loader import data_loader
from app.services.preferred_suppliers import PreferredSupplierService

def test_service():
    service = PreferredSupplierService(data_loader)
    
    # 1. Test ITM-1048 as of 2026-11-01
    pref_1048 = service.get_preferred_suppliers_for_item("ITM-1048", "2026-11-01")
    print("ITM-1048 ranked:")
    for p in pref_1048:
        print(f"  Rank {p.rank}: {p.supplier_id} ({p.supplier_name}) - Score: {p.composite_score}, POs: {p.po_count_548d}, Recency: {p.recency_score}, Contract: {p.has_contract}, OnTime: {p.on_time_pct}%, Q: {p.quality_rating}, RefPrice: {p.reference_price}")
    
    assert pref_1048[0].supplier_id == "S029", f"Expected S029, got {pref_1048[0].supplier_id}"
    assert pref_1048[1].supplier_id == "S030", f"Expected S030, got {pref_1048[1].supplier_id}"
    # check S031 is excluded
    assert "S031" not in [p.supplier_id for p in pref_1048], "S031 should be excluded as Inactive"
    
    # 2. Test ITM-1036 as of 2026-11-01
    pref_1036 = service.get_preferred_suppliers_for_item("ITM-1036", "2026-11-01")
    print("\nITM-1036 ranked:")
    for p in pref_1036:
        print(f"  Rank {p.rank}: {p.supplier_id} ({p.supplier_name}) - Score: {p.composite_score}")
    assert pref_1036[0].supplier_id == "S023"
    assert pref_1036[1].supplier_id == "S022"
    assert pref_1036[2].supplier_id == "S024"
    
    # 3. Test ITM-1016 as of 2026-11-01
    pref_1016 = service.get_preferred_suppliers_for_item("ITM-1016", "2026-11-01")
    print("\nITM-1016 ranked:")
    for p in pref_1016:
        print(f"  Rank {p.rank}: {p.supplier_id} ({p.supplier_name}) - Score: {p.composite_score}")
    assert pref_1016[0].supplier_id == "S009"
    assert pref_1016[1].supplier_id == "S010"

    print("\nALL PREFERRED SUPPLIER TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_service()
