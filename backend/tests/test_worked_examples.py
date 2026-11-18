import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.db.seed import seed_database
from app.infrastructure.repositories.sql_repositories import (
    SQLItemRepository, SQLSupplierRepository, SQLContractRepository,
    SQLPOHistoryRepository, SQLRequirementRepository, SQLPolicyRepository
)
from app.application.use_cases.process_batch_use_case import ProcessBatchUseCase
from app.application.dto.schemas import PRLineDTO

def test_worked_examples():
    seed_database()
    db = SessionLocal()

    # Ensure baseline policy 5.0 is active
    from app.db.models import PolicyVersionModel
    for r in db.query(PolicyVersionModel).all():
        r.is_active = (r.version == "5.0")
    db.commit()

    use_case = ProcessBatchUseCase(
        item_repo=SQLItemRepository(db),
        supplier_repo=SQLSupplierRepository(db),
        contract_repo=SQLContractRepository(db),
        po_history_repo=SQLPOHistoryRepository(db),
        requirement_repo=SQLRequirementRepository(db),
        policy_repo=SQLPolicyRepository(db)
    )

    print("=== RUNNING WORKED EXAMPLES TEST SUITE (CLEAN ARCHITECTURE) ===")

    # 1. Contract PO: PR-26-00019/1
    pr1 = PRLineDTO(
        pr_no="PR-26-00019", pr_line=1, created_at="2026-11-04 12:40",
        plant="PUN1", item_code="ITM-1002", description="MS sheet 3mm 1250x2500",
        quantity=15, uom="NOS", need_by_date="2026-11-15", urgency="Normal"
    )
    res1 = use_case.execute([pr1]).decisions[0]
    print(f"Ex 1: Route={res1.route}, Supp={res1.supplier_id}, Price={res1.unit_price}, Val={res1.group_value_inr}")
    assert res1.route == "CONTRACT_PO"
    assert res1.supplier_id == "S001"
    assert round(res1.unit_price) == 9169
    assert round(res1.group_value_inr) == 137531

    # 2. Contract that exists only as PDF: PR-26-00045/1
    pr2 = PRLineDTO(
        pr_no="PR-26-00045", pr_line=1, created_at="2026-11-18 10:50",
        plant="CHK1", item_code="ITM-1037", description="Solenoid valve 5/2 1/4 inch",
        quantity=11, uom="NOS", need_by_date="2026-12-13", urgency="Normal"
    )
    res2 = use_case.execute([pr2]).decisions[0]
    print(f"Ex 2: Route={res2.route}, Supp={res2.supplier_id}, Price={res2.unit_price}, Val={res2.group_value_inr}")
    assert res2.route == "CONTRACT_PO"
    assert res2.supplier_id == "S021"
    assert round(res2.unit_price) == 2439
    assert round(res2.group_value_inr) == 26829

    # 3. Contract ceiling nearly used up: PR-26-00004/1 and PR-26-00026/1
    pr3_a = PRLineDTO(
        pr_no="PR-26-00004", pr_line=1, created_at="2026-11-02 15:15",
        plant="CHK1", item_code=None, description="brg 6308 ZZ for maintenance",
        quantity=210, uom="NOS", estimated_unit_price=715.25, need_by_date="2026-11-26", urgency="Normal"
    )
    pr3_b = PRLineDTO(
        pr_no="PR-26-00026", pr_line=1, created_at="2026-11-02 15:20",
        plant="CHK1", item_code="ITM-1022", description="Ball bearing 6308-ZZ",
        quantity=170, uom="NOS", need_by_date="2026-11-23", urgency="Normal"
    )
    res3 = use_case.execute([pr3_a, pr3_b]).decisions
    print(f"Ex 3: Clubbed into Group {res3[0].group_id}, Route={res3[0].route}, Val={res3[0].group_value_inr}, Sug={res3[0].suggested_supplier_ids}")
    assert res3[0].group_id == res3[1].group_id
    assert res3[0].route == "RFQ"
    assert round(res3[0].group_value_inr) == 220256
    assert "S014" in res3[0].suggested_supplier_ids

    # 5. Split PRs clubbed into one requirement: PR-26-00146, 144, 145
    pr5_a = PRLineDTO(pr_no="PR-26-00146", pr_line=1, created_at="2026-11-02 09:40", plant="CHK1", item_code="ITM-1038", description="Hydraulic oil HLP 68", quantity=270, uom="LTR", need_by_date="2026-11-19", urgency="Normal")
    pr5_b = PRLineDTO(pr_no="PR-26-00144", pr_line=1, created_at="2026-11-03 09:30", plant="CHK1", item_code="ITM-1038", description="Hydraulic oil HLP 68", quantity=190, uom="LTR", need_by_date="2026-11-15", urgency="Normal")
    pr5_c = PRLineDTO(pr_no="PR-26-00145", pr_line=1, created_at="2026-11-05 08:40", plant="CHK1", item_code="ITM-1038", description="Hydraulic oil HLP 68", quantity=300, uom="LTR", need_by_date="2026-11-21", urgency="Normal")
    res5 = use_case.execute([pr5_a, pr5_b, pr5_c]).decisions
    print(f"Ex 5: Clubbed Group={res5[0].group_id}, Route={res5[0].route}, Supp={res5[0].supplier_id}, Val={res5[0].group_value_inr}")
    assert res5[0].group_id == res5[1].group_id == res5[2].group_id
    assert res5[0].route == "SPOT_PO"
    assert res5[0].supplier_id == "S024"
    assert round(res5[0].group_value_inr) == 126472

    # 7. Free-text item matched: PR-26-00088/1
    pr7 = PRLineDTO(
        pr_no="PR-26-00088", pr_line=1, created_at="2026-11-06 15:00",
        plant="PUN1", item_code=None, description="hyd hose 1/2 inch 2 wire",
        quantity=250, uom="MTR", need_by_date="2026-11-28", urgency="Normal"
    )
    res7 = use_case.execute([pr7]).decisions[0]
    print(f"Ex 7: Match={res7.resolved_item_code}, Route={res7.route}, Supp={res7.supplier_id}, Val={res7.group_value_inr}")
    assert res7.resolved_item_code == "ITM-1035"
    assert res7.route == "SPOT_PO"
    assert res7.supplier_id == "S023"
    assert round(res7.group_value_inr) == 97955

    # 8. Emergency PO: PR-26-00059/1
    pr8 = PRLineDTO(
        pr_no="PR-26-00059", pr_line=1, created_at="2026-11-06 18:50",
        plant="PUN1", item_code="ITM-1026", description="Gearbox oil seal 45x62x8",
        quantity=2380, uom="NOS", need_by_date="2026-11-25", urgency="Emergency"
    )
    res8 = use_case.execute([pr8]).decisions[0]
    print(f"Ex 8: Route={res8.route}, Supp={res8.supplier_id}, Val={res8.group_value_inr}")
    assert res8.route == "EMERGENCY_PO"
    assert res8.supplier_id == "S014"
    assert round(res8.group_value_inr) == 253184

    # 9. RFQ: above PO limit: PR-26-00089/1
    pr9 = PRLineDTO(
        pr_no="PR-26-00089", pr_line=1, created_at="2026-11-05 18:40",
        plant="PUN1", item_code=None, description="CMM calibration service",
        quantity=5, uom="JOB", need_by_date="2026-11-30", urgency="Normal"
    )
    res9 = use_case.execute([pr9]).decisions[0]
    print(f"Ex 9: Route={res9.route}, Val={res9.group_value_inr}, Sug={res9.suggested_supplier_ids}")
    assert res9.route == "RFQ"
    assert round(res9.group_value_inr) == 336562

    # 10. RFQ: small but never bought: PR-26-00050/1
    pr10 = PRLineDTO(
        pr_no="PR-26-00050", pr_line=1, created_at="2026-11-02 10:20",
        plant="PUN1", item_code="ITM-1006", description="Aluminium plate 6061 10mm",
        quantity=220, uom="KG", need_by_date="2026-11-15", urgency="Normal"
    )
    res10 = use_case.execute([pr10]).decisions[0]
    print(f"Ex 10: Route={res10.route}, Val={res10.group_value_inr}, Sug={res10.suggested_supplier_ids}")
    assert res10.route == "RFQ"
    assert round(res10.group_value_inr) == 80300

    # 11. RFP: PR-26-00100/1
    pr11 = PRLineDTO(
        pr_no="PR-26-00100", pr_line=1, created_at="2026-11-04 13:05",
        plant="CHK1", item_code="ITM-1034", description="Encoder for CNC spindle (Vertex)",
        quantity=50, uom="NOS", need_by_date="2026-11-24", urgency="Normal"
    )
    res11 = use_case.execute([pr11]).decisions[0]
    print(f"Ex 11: Route={res11.route}, Val={res11.group_value_inr}")
    assert res11.route == "RFP"
    assert round(res11.group_value_inr) == 2070780

    # 12. Capex: PR-26-00047/1
    pr12 = PRLineDTO(
        pr_no="PR-26-00047", pr_line=1, created_at="2026-11-03 14:00",
        plant="PUN1", item_code=None, description="eot crane 5 ton",
        quantity=4, uom="NOS", need_by_date="2026-12-01", urgency="Normal"
    )
    res12 = use_case.execute([pr12]).decisions[0]
    print(f"Ex 12: Route={res12.route}, Val={res12.group_value_inr}")
    assert res12.route == "CAPEX_SOURCING"
    assert round(res12.group_value_inr) == 6036704

    # 13. New item: PR-26-00170/1
    pr13 = PRLineDTO(
        pr_no="PR-26-00170", pr_line=1, created_at="2026-11-05 10:40",
        plant="PUN1", item_code=None, description="Drinking water purifier 50 LPH",
        quantity=1, uom="NOS", estimated_unit_price=141100, need_by_date="2026-11-13", urgency="Normal"
    )
    res13 = use_case.execute([pr13]).decisions[0]
    print(f"Ex 13: Route={res13.route}, Val={res13.group_value_inr}, Sug={res13.suggested_supplier_ids}")
    assert res13.route == "NEW_ITEM_SOURCING"
    assert res13.resolved_item_code == "NEW"
    assert round(res13.group_value_inr) == 141100
    assert res13.suggested_supplier_ids is None

    db.close()
    print("\nALL WORKED EXAMPLES MATCH 100% PERFECTLY (CLEAN ARCHITECTURE)!")

if __name__ == "__main__":
    test_worked_examples()
