import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api():
    # 1. Health check
    res = client.get("/")
    assert res.status_code == 200
    print("Health check passed:", res.json())

    # 2. Policy endpoints
    res = client.get("/api/policy/current")
    assert res.status_code == 200
    print("Current policy version:", res.json()["version"])

    # 3. Chat intake endpoint
    res = client.post("/api/chat", json={
        "role": "user",
        "content": "need 200 nitrile gloves for Chakan by next Friday"
    })
    assert res.status_code == 200
    chat_res = res.json()
    print("Chat parsed PR:", chat_res["parsed_pr"])
    assert chat_res["is_complete"] is True

    # 4. Preferred suppliers endpoint
    res = client.get("/api/suppliers/preferred?item_code=ITM-1048&date=2026-11-01")
    assert res.status_code == 200
    pref = res.json()
    print("ITM-1048 preferred supplier #1:", pref["ranked_suppliers"][0]["supplier_id"])
    assert pref["ranked_suppliers"][0]["supplier_id"] == "S029"

    # 5. Process Batch
    csv_path = Path(__file__).resolve().parent.parent.parent / "Cantill_FullStack_Task_Kit" / "pr_batches" / "sample_pr_batch.csv"
    with open(csv_path, "rb") as f:
        res = client.post("/api/process-batch", files={"file": ("sample_pr_batch.csv", f, "text/csv")})
    assert res.status_code == 200
    batch_res = res.json()
    print("Batch processed:", batch_res["total_lines"], "lines,", batch_res["unique_requirements"], "requirements,", batch_res["consolidated_pos"], "POs")
    assert batch_res["total_lines"] == 186

    # 6. Export Decisions CSV
    res = client.get("/api/export-decisions")
    assert res.status_code == 200
    csv_lines = res.text.strip().splitlines()
    print("Exported CSV line count (including header):", len(csv_lines))
    assert len(csv_lines) == 187 # 1 header + 186 PR lines
    print("Header:", csv_lines[0])

    # 7. Buyer Workspace
    res = client.get("/api/buyer/requirements")
    assert res.status_code == 200
    buyer_res = res.json()
    print("Buyer workspace loaded", len(buyer_res["requirements"]), "requirements")

    # 8. Contracts list
    res = client.get("/api/contracts")
    assert res.status_code == 200
    print("Contracts loaded:", len(res.json()))

    print("\nALL API ENDPOINTS TESTED AND FUNCTIONING 100% PERFECTLY!")

if __name__ == "__main__":
    test_api()
