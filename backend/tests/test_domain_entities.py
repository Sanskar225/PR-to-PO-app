import sys
from pathlib import Path
from datetime import datetime, date, timedelta
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.domain.entities.pr_line import PurchaseRequisitionLine, UrgencyLevel
from app.domain.entities.requirement import RequirementGroup
from app.domain.entities.contract import RateContract
from app.domain.entities.purchase_order import ConsolidatedPurchaseOrder
from app.core.exceptions import ContractCeilingExceededException

def test_requirement_group_invariants():
    pr1 = PurchaseRequisitionLine(
        pr_no="PR-01", pr_line=1, created_at=datetime(2026, 11, 2, 9, 30),
        requester="Alice", department="Stores", plant="CHK1",
        item_code="ITM-1038", description="Hydraulic oil", quantity=270,
        uom="LTR", estimated_unit_price=160, need_by_date=date(2026, 11, 19),
        resolved_item_code="ITM-1038"
    )
    group = RequirementGroup(group_id="REQ-0001", resolved_item_code="ITM-1038", plant="CHK1", first_pr=pr1)

    # 1. Same item, same plant, within 14d, need-by within 7d -> CAN JOIN
    pr2 = PurchaseRequisitionLine(
        pr_no="PR-02", pr_line=1, created_at=datetime(2026, 11, 4, 10, 0),
        requester="Bob", department="Stores", plant="CHK1",
        item_code="ITM-1038", description="Hydraulic oil", quantity=190,
        uom="LTR", estimated_unit_price=160, need_by_date=date(2026, 11, 16),
        resolved_item_code="ITM-1038"
    )
    assert group.can_absorb(pr2) is True
    group.add_line(pr2)
    assert group.total_quantity == 460

    # 2. Different plant -> CANNOT JOIN
    pr_diff_plant = PurchaseRequisitionLine(
        pr_no="PR-03", pr_line=1, created_at=datetime(2026, 11, 4, 10, 0),
        requester="Charlie", department="Stores", plant="PUN1",
        item_code="ITM-1038", description="Hydraulic oil", quantity=100,
        uom="LTR", estimated_unit_price=160, need_by_date=date(2026, 11, 16),
        resolved_item_code="ITM-1038"
    )
    assert group.can_absorb(pr_diff_plant) is False

    # 3. Created beyond 14 days -> CANNOT JOIN
    pr_late = PurchaseRequisitionLine(
        pr_no="PR-04", pr_line=1, created_at=datetime(2026, 11, 20, 10, 0),
        requester="Dave", department="Stores", plant="CHK1",
        item_code="ITM-1038", description="Hydraulic oil", quantity=100,
        uom="LTR", estimated_unit_price=160, need_by_date=date(2026, 11, 19),
        resolved_item_code="ITM-1038"
    )
    assert group.can_absorb(pr_late) is False

    print("RequirementGroup Domain Invariants: PASSED")

def test_contract_ceiling_invariants():
    c = RateContract(
        contract_id="RC-TEST-01", supplier_id="S001", supplier_name="Test Supp",
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        value_cap=100000.0, consumed_value=90000.0
    )
    assert c.remaining_ceiling == 10000.0
    assert c.can_accommodate(8000.0) is True
    assert c.can_accommodate(12000.0) is False

    c.consume_ceiling(8000.0)
    assert c.consumed_value == 98000.0
    assert c.remaining_ceiling == 2000.0

    # Violating invariant must raise ContractCeilingExceededException
    try:
        c.consume_ceiling(5000.0)
        assert False, "Should have raised ContractCeilingExceededException"
    except ContractCeilingExceededException:
        pass

    print("RateContract Ceiling Invariants: PASSED")

def test_po_consolidation_invariants():
    pr1 = PurchaseRequisitionLine(
        pr_no="PR-01", pr_line=1, created_at=datetime(2026, 11, 2, 14, 0),
        requester="Alice", department="Stores", plant="PUN1",
        item_code="ITM-1009", description="Hex bolt", quantity=3920,
        uom="NOS", estimated_unit_price=7, need_by_date=date(2026, 11, 25),
        resolved_item_code="ITM-1009"
    )
    req1 = RequirementGroup(group_id="REQ-0001", resolved_item_code="ITM-1009", plant="PUN1", first_pr=pr1)
    req1.decision = "PO"
    req1.route = "CONTRACT_PO"
    req1.supplier_id = "S007"
    req1.group_value_inr = 27675.0

    po = ConsolidatedPurchaseOrder(
        po_id="PO-0001", supplier_id="S007", plant="PUN1", route="CONTRACT_PO",
        first_requirement_created_at=datetime(2026, 11, 2, 14, 0)
    )
    po.add_requirement(req1)

    # Same supplier, same plant, same route within 24h -> CAN CONSOLIDATE
    pr2 = PurchaseRequisitionLine(
        pr_no="PR-02", pr_line=1, created_at=datetime(2026, 11, 3, 10, 0), # 20 hrs later
        requester="Bob", department="Stores", plant="PUN1",
        item_code="ITM-1009", description="Hex bolt", quantity=1140,
        uom="NOS", estimated_unit_price=7, need_by_date=date(2026, 11, 12),
        resolved_item_code="ITM-1009"
    )
    req2 = RequirementGroup(group_id="REQ-0002", resolved_item_code="ITM-1009", plant="PUN1", first_pr=pr2)
    req2.decision = "PO"
    req2.route = "CONTRACT_PO"
    req2.supplier_id = "S007"
    req2.group_value_inr = 8048.0

    assert po.can_consolidate(req2, window_hours=24) is True
    po.add_requirement(req2)
    assert req2.po_id == "PO-0001"

    # Beyond 24h -> CANNOT CONSOLIDATE
    pr3 = PurchaseRequisitionLine(
        pr_no="PR-03", pr_line=1, created_at=datetime(2026, 11, 5, 10, 0), # 68 hrs later
        requester="Dave", department="Stores", plant="PUN1",
        item_code="ITM-1009", description="Hex bolt", quantity=500,
        uom="NOS", estimated_unit_price=7, need_by_date=date(2026, 11, 20),
        resolved_item_code="ITM-1009"
    )
    req3 = RequirementGroup(group_id="REQ-0003", resolved_item_code="ITM-1009", plant="PUN1", first_pr=pr3)
    req3.decision = "PO"
    req3.route = "CONTRACT_PO"
    req3.supplier_id = "S007"

    assert po.can_consolidate(req3, window_hours=24) is False

    print("PO Consolidation Domain Invariants: PASSED")

if __name__ == "__main__":
    test_requirement_group_invariants()
    test_contract_ceiling_invariants()
    test_po_consolidation_invariants()
    print("\nALL DOMAIN INVARIANT TESTS PASSED 100%!")
