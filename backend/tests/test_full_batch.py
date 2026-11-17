import sys
import pandas as pd
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import PR_BATCHES_DIR
from app.db.session import SessionLocal
from app.db.seed import seed_database
from app.infrastructure.repositories.sql_repositories import (
    SQLItemRepository, SQLSupplierRepository, SQLContractRepository,
    SQLPOHistoryRepository, SQLRequirementRepository, SQLPolicyRepository
)
from app.application.use_cases.process_batch_use_case import ProcessBatchUseCase
from app.application.dto.schemas import PRLineDTO

def test_full_batch():
    seed_database()
    db = SessionLocal()

    use_case = ProcessBatchUseCase(
        item_repo=SQLItemRepository(db),
        supplier_repo=SQLSupplierRepository(db),
        contract_repo=SQLContractRepository(db),
        po_history_repo=SQLPOHistoryRepository(db),
        requirement_repo=SQLRequirementRepository(db),
        policy_repo=SQLPolicyRepository(db)
    )

    batch_csv = PR_BATCHES_DIR / "sample_pr_batch.csv"
    df = pd.read_csv(batch_csv)

    dtos = []
    for _, row in df.iterrows():
        code_val = str(row["item_code"]).strip() if pd.notna(row.get("item_code")) else None
        if code_val in ["", "nan", "None"]:
            code_val = None
        est_p = float(row["estimated_unit_price"]) if pd.notna(row.get("estimated_unit_price")) else None

        dtos.append(PRLineDTO(
            pr_no=str(row["pr_no"]).strip(),
            pr_line=int(row["pr_line"]),
            created_at=str(row["created_at"]).strip(),
            requester=str(row.get("requester", "")).strip(),
            department=str(row.get("department", "")).strip(),
            plant=str(row["plant"]).strip(),
            item_code=code_val,
            description=str(row["description"]).strip(),
            quantity=float(row["quantity"]),
            uom=str(row.get("uom", "NOS")).strip(),
            estimated_unit_price=est_p,
            need_by_date=str(row["need_by_date"]).strip(),
            urgency=str(row.get("urgency", "Normal")).strip()
        ))

    print(f"Executing Clean Architecture Batch Use Case with {len(dtos)} lines...")
    result = use_case.execute(dtos, filename="sample_pr_batch.csv")

    print(f"Total Lines Processed: {result.total_lines}")
    print(f"Unique Requirements Clubbed: {result.unique_requirements}")
    print(f"Consolidated POs (24h window): {result.consolidated_pos}")
    print(f"Total Value (INR): ₹{result.total_value_inr:,.2f}")

    print("\n--- Route Distribution ---")
    for r, count in sorted(result.route_distribution.items()):
        print(f"  {r}: {count}")

    # Check zero blocked suppliers
    s_repo = SQLSupplierRepository(db)
    suppliers = {s.supplier_id: s for s in s_repo.get_all()}
    blocked_count = 0
    for d in result.decisions:
        if d.supplier_id:
            s = suppliers.get(d.supplier_id)
            if s and not s.is_eligible:
                blocked_count += 1

    print(f"\nBlocked/Inactive suppliers selected: {blocked_count} (Must be 0!)")
    assert blocked_count == 0, "No blocked/inactive suppliers must ever be chosen!"
    assert result.total_lines == 186
    assert result.unique_requirements == 151
    assert result.consolidated_pos == 84

    db.close()
    print("\nFULL 186-LINE BATCH TEST PASSED 100%!")

if __name__ == "__main__":
    test_full_batch()
