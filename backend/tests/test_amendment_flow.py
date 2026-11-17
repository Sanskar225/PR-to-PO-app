import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_amendment():
    print("=== TESTING POLICY AMENDMENT FLOW (BLIND TEST SIMULATION) ===")
    
    # 1. Check current policy version
    res = client.get("/api/policy/current")
    assert res.json()["version"] == "5.0"
    print("Base Version:", res.json()["version"])

    # 2. Submit Amendment
    amend_text = """
    POLICY AMENDMENT NOTICE - CORVO PROCUREMENT
    Effective Date: 2026-12-01
    Version: 5.1
    1. Spot PO limit is increased to INR 300,000.
    2. Emergency PO threshold is increased to INR 750,000.
    """
    res = client.post("/api/policy/amend-text", json={"amendment_text": amend_text})
    assert res.status_code == 200
    diff = res.json()
    print("Generated Diff Summary:")
    for s in diff["summary_of_changes"]:
        print("  *", s)
    assert diff["new_version"] == "5.1"

    # 3. Approve Amendment
    res = client.post("/api/policy/approve", json={"version": "5.1"})
    assert res.status_code == 200
    print("Approved new version:", res.json()["active_policy"]["version"])

    # 4. Verify Active Policy is now 5.1
    res = client.get("/api/policy/current")
    assert res.json()["version"] == "5.1"
    print("Active version verified:", res.json()["version"])

    # 5. Reprocess sample batch under 5.1
    csv_path = Path(__file__).resolve().parent.parent.parent / "Cantill_FullStack_Task_Kit" / "pr_batches" / "sample_pr_batch.csv"
    with open(csv_path, "rb") as f:
        res = client.post("/api/process-batch", files={"file": ("sample_pr_batch.csv", f, "text/csv")})
    assert res.status_code == 200
    batch_res = res.json()
    print("Run 2 processed under policy:", batch_res["policy_version_applied"])
    print("Run 2 Route distribution with higher 3L spot limit:", batch_res["route_distribution"])
    assert batch_res["policy_version_applied"] == "5.1"

    # Reset back to 5.0 for clean baseline
    client.post("/api/policy/approve", json={"version": "5.0"})
    print("Reset back to 5.0 baseline. Amendment test passed 100%!")

if __name__ == "__main__":
    test_amendment()
