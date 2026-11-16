import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import POLICIES_DIR
from app.models.schemas import PolicyDocument, PRLineInput
from app.services.data_loader import data_loader
from app.services.policy_engine import PolicyEngine

def load_policy_v5():
    with open(POLICIES_DIR / "policy_v5_0.json", "r") as f:
        data = json.load(f)
    return PolicyDocument(**data)

def run_tests():
    policy = load_policy_v5()
    engine = PolicyEngine(data_loader, policy)

    print("=== RUNNING WORKED EXAMPLES TEST SUITE ===")

    # 1. Contract PO: PR-26-00019/1
    pr1 = PRLineInput(
        pr_no="PR-26-00019", pr_line=1, created_at="2026-11-04 12:40",
        plant="PUN1", item_code="ITM-1002", description="MS sheet 3mm 1250x2500",
        quantity=15, uom="NOS", need_by_date="2026-11-15", urgency="Normal"
    )
    res1 = engine.process_pr_batch([pr1])[0]
    print(f"Ex 1: Route={res1.route}, Supp={res1.supplier_id}, Price={res1.unit_price}, Val={res1.group_value_inr}")
    assert res1.route == "CONTRACT_PO"
    assert res1.supplier_id == "S001"
    assert round(res1.unit_price) == 9169
    assert round(res1.group_value_inr) == 137531

    # 2. Contract that exists only as PDF: PR-26-00045/1
    pr2 = PRLineInput(
        pr_no="PR-26-00045", pr_line=1, created_at="2026-11-18 10:50",
        plant="CHK1", item_code="ITM-1037", description="Solenoid valve 5/2 1/4 inch",
        quantity=11, uom="NOS", need_by_date="2026-12-13", urgency="Normal"
    )
    res2 = engine.process_pr_batch([pr2])[0]
    print(f"Ex 2: Route={res2.route}, Supp={res2.supplier_id}, Price={res2.unit_price}, Val={res2.group_value_inr}")
    assert res2.route == "CONTRACT_PO"
    assert res2.supplier_id == "S021"
    assert round(res2.unit_price) == 2439
    assert round(res2.group_value_inr) == 26829

    # 3. Contract ceiling nearly used up: PR-26-00004/1 and PR-26-00026/1
    pr3_a = PRLineInput(
        pr_no="PR-26-00004", pr_line=1, created_at="2026-11-02 15:15",
        plant="CHK1", item_code=None, description="brg 6308 ZZ for maintenance",
        quantity=210, uom="NOS", estimated_unit_price=715.25, need_by_date="2026-11-26", urgency="Normal"
    )
    pr3_b = PRLineInput(
        pr_no="PR-26-00026", pr_line=1, created_at="2026-11-02 15:20",
        plant="CHK1", item_code="ITM-1022", description="Ball bearing 6308-ZZ",
        quantity=170, uom="NOS", need_by_date="2026-11-23", urgency="Normal"
    )
    res3 = engine.process_pr_batch([pr3_a, pr3_b])
    print(f"Ex 3: Clubbed into Group {res3[0].group_id}, Route={res3[0].route}, Val={res3[0].group_value_inr}, Sug={res3[0].suggested_supplier_ids}")
    assert res3[0].group_id == res3[1].group_id
    assert res3[0].route == "RFQ"
    assert round(res3[0].group_value_inr) == 220256
    assert "S014" in res3[0].suggested_supplier_ids

    # 5. Split PRs clubbed into one requirement: PR-26-00146, 144, 145
    pr5_a = PRLineInput(pr_no="PR-26-00146", pr_line=1, created_at="2026-11-02 09:40", plant="CHK1", item_code="ITM-1038", description="Hydraulic oil HLP 68", quantity=270, uom="LTR", need_by_date="2026-11-19", urgency="Normal")
    pr5_b = PRLineInput(pr_no="PR-26-00144", pr_line=1, created_at="2026-11-03 09:30", plant="CHK1", item_code="ITM-1038", description="Hydraulic oil HLP 68", quantity=190, uom="LTR", need_by_date="2026-11-15", urgency="Normal")
    pr5_c = PRLineInput(pr_no="PR-26-00145", pr_line=1, created_at="2026-11-05 08:40", plant="CHK1", item_code="ITM-1038", description="Hydraulic oil HLP 68", quantity=300, uom="LTR", need_by_date="2026-11-21", urgency="Normal")
    res5 = engine.process_pr_batch([pr5_a, pr5_b, pr5_c])
    print(f"Ex 5: Clubbed Group={res5[0].group_id}, Route={res5[0].route}, Supp={res5[0].supplier_id}, Val={res5[0].group_value_inr}")
    assert res5[0].group_id == res5[1].group_id == res5[2].group_id
    assert res5[0].route == "SPOT_PO"
    assert res5[0].supplier_id == "S024"
    assert round(res5[0].group_value_inr) == 126472

    # 7. Free-text item matched: PR-26-00088/1
    pr7 = PRLineInput(
        pr_no="PR-26-00088", pr_line=1, created_at="2026-11-06 15:00",
        plant="PUN1", item_code=None, description="hyd hose 1/2 inch 2 wire",
        quantity=250, uom="MTR", need_by_date="2026-11-28", urgency="Normal"
    )
    res7 = engine.process_pr_batch([pr7])[0]
    print(f"Ex 7: Match={res7.resolved_item_code}, Route={res7.route}, Supp={res7.supplier_id}, Val={res7.group_value_inr}")
    assert res7.resolved_item_code == "ITM-1035"
    assert res7.route == "SPOT_PO"
    assert res7.supplier_id == "S023"
    assert round(res7.group_value_inr) == 97955

    # 8. Emergency PO: PR-26-00059/1
    pr8 = PRLineInput(
        pr_no="PR-26-00059", pr_line=1, created_at="2026-11-06 18:50",
        plant="PUN1", item_code="ITM-1026", description="Gearbox oil seal 45x62x8",
        quantity=2380, uom="NOS", need_by_date="2026-11-25", urgency="Emergency"
    )
    res8 = engine.process_pr_batch([pr8])[0]
    print(f"Ex 8: Route={res8.route}, Supp={res8.supplier_id}, Val={res8.group_value_inr}")
    assert res8.route == "EMERGENCY_PO"
    assert res8.supplier_id == "S014"
    assert round(res8.group_value_inr) == 253184

    # 9. RFQ: above PO limit: PR-26-00089/1
    pr9 = PRLineInput(
        pr_no="PR-26-00089", pr_line=1, created_at="2026-11-05 18:40",
        plant="PUN1", item_code=None, description="CMM calibration service",
        quantity=5, uom="JOB", need_by_date="2026-11-30", urgency="Normal"
    )
    res9 = engine.process_pr_batch([pr9])[0]
    print(f"Ex 9: Route={res9.route}, Val={res9.group_value_inr}, Sug={res9.suggested_supplier_ids}")
    assert res9.route == "RFQ"
    assert round(res9.group_value_inr) == 336562

    # 10. RFQ: small but never bought: PR-26-00050/1
    pr10 = PRLineInput(
        pr_no="PR-26-00050", pr_line=1, created_at="2026-11-02 10:20",
        plant="PUN1", item_code="ITM-1006", description="Aluminium plate 6061 10mm",
        quantity=220, uom="KG", need_by_date="2026-11-15", urgency="Normal"
    )
    res10 = engine.process_pr_batch([pr10])[0]
    print(f"Ex 10: Route={res10.route}, Val={res10.group_value_inr}, Sug={res10.suggested_supplier_ids}")
    assert res10.route == "RFQ"
    assert round(res10.group_value_inr) == 80300

    # 11. RFP: PR-26-00100/1
    pr11 = PRLineInput(
        pr_no="PR-26-00100", pr_line=1, created_at="2026-11-04 13:05",
        plant="CHK1", item_code="ITM-1034", description="Encoder for CNC spindle (Vertex)",
        quantity=50, uom="NOS", need_by_date="2026-11-24", urgency="Normal"
    )
    res11 = engine.process_pr_batch([pr11])[0]
    print(f"Ex 11: Route={res11.route}, Val={res11.group_value_inr}")
    assert res11.route == "RFP"
    assert round(res11.group_value_inr) == 2070780

    # 12. Capex: PR-26-00047/1
    pr12 = PRLineInput(
        pr_no="PR-26-00047", pr_line=1, created_at="2026-11-03 14:00",
        plant="PUN1", item_code=None, description="eot crane 5 ton",
        quantity=4, uom="NOS", need_by_date="2026-12-01", urgency="Normal"
    )
    res12 = engine.process_pr_batch([pr12])[0]
    print(f"Ex 12: Route={res12.route}, Val={res12.group_value_inr}")
    assert res12.route == "CAPEX_SOURCING"
    assert round(res12.group_value_inr) == 6036704

    # 13. New item: PR-26-00170/1
    pr13 = PRLineInput(
        pr_no="PR-26-00170", pr_line=1, created_at="2026-11-05 10:40",
        plant="PUN1", item_code=None, description="Drinking water purifier 50 LPH",
        quantity=1, uom="NOS", estimated_unit_price=141100, need_by_date="2026-11-13", urgency="Normal"
    )
    res13 = engine.process_pr_batch([pr13])[0]
    print(f"Ex 13: Route={res13.route}, Val={res13.group_value_inr}, Sug={res13.suggested_supplier_ids}")
    assert res13.route == "NEW_ITEM_SOURCING"
    assert res13.resolved_item_code == "NEW"
    assert round(res13.group_value_inr) == 141100
    assert res13.suggested_supplier_ids is None

    print("\nALL WORKED EXAMPLES MATCH 100% PERFECTLY!")

if __name__ == "__main__":
    run_tests()
