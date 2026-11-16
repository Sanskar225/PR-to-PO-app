import sys
import json
import pandas as pd
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import POLICIES_DIR, PR_BATCHES_DIR
from app.models.schemas import PolicyDocument, PRLineInput
from app.services.data_loader import data_loader
from app.services.policy_engine import PolicyEngine

def test_full_batch():
    with open(POLICIES_DIR / "policy_v5_0.json", "r") as f:
        policy = PolicyDocument(**json.load(f))
    engine = PolicyEngine(data_loader, policy)

    batch_csv = PR_BATCHES_DIR / "sample_pr_batch.csv"
    df = pd.read_csv(batch_csv)
    
    pr_lines = []
    for _, row in df.iterrows():
        pr_lines.append(PRLineInput(
            pr_no=str(row["pr_no"]).strip(),
            pr_line=int(row["pr_line"]),
            created_at=str(row["created_at"]).strip(),
            requester=str(row.get("requester", "")).strip(),
            department=str(row.get("department", "")).strip(),
            plant=str(row["plant"]).strip(),
            item_code=str(row["item_code"]).strip() if pd.notna(row.get("item_code")) else None,
            description=str(row["description"]).strip(),
            quantity=float(row["quantity"]),
            uom=str(row.get("uom", "NOS")).strip(),
            estimated_unit_price=float(row["estimated_unit_price"]) if pd.notna(row.get("estimated_unit_price")) else None,
            need_by_date=str(row["need_by_date"]).strip(),
            urgency=str(row.get("urgency", "Normal")).strip()
        ))

    print(f"Loaded {len(pr_lines)} PR lines from sample_pr_batch.csv")
    decisions = engine.process_pr_batch(pr_lines)
    print(f"Generated {len(decisions)} decision records.")

    # Breakdown by route
    routes = {}
    blocked_count = 0
    total_val = 0.0
    for d in decisions:
        routes[d.route] = routes.get(d.route, 0) + 1
        total_val += d.group_value_inr
        if d.supplier_id:
            supp = data_loader.suppliers.get(d.supplier_id)
            if supp and supp.status != "Active":
                blocked_count += 1

    print("\n--- Route Distribution ---")
    for r, count in sorted(routes.items()):
        print(f"  {r}: {count}")

    print(f"\nBlocked/Inactive suppliers selected: {blocked_count} (Must be 0!)")
    assert blocked_count == 0, "No blocked/inactive suppliers must ever be chosen!"

    # Check distinct PO count
    pos = set(d.po_id for d in decisions if d.po_id)
    groups = set(d.group_id for d in decisions)
    print(f"Total Unique Requirement Groups: {len(groups)}")
    print(f"Total Unique Consolidated POs: {len(pos)}")
    print("Full Batch Test Passed with Flying Colors!")

if __name__ == "__main__":
    test_full_batch()
