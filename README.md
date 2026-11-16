# Corvo Engineering — Policy-Driven PR-to-PO Decision Engine

> **Cantill.ai Full-stack Intern Challenge (Round 1)**  
> Automated, policy-driven procurement engine that ingests Purchase Requisitions (PRs) via chat or batch CSV and determines whether to place a Purchase Order (PO) or initiate Sourcing (RFQ/RFP/Capex) based on declarative, versioned policy rules.

---

## 🌟 Key Features

1. **Chat Intake Assistant**: Natural language chat interface that parses requirements, resolves items (including free-text short forms), asks for missing attributes (plant, qty, need-by date), and confirms PR creation.
2. **Policy-as-Data Engine (v5.0)**:
   - **Anti-Splitting Clubbing**: Groups similar PR lines (same item, plant, within 14 days creation, within ±7 days need-by).
   - **Valuation Cascade**: Valued by contract rate $\rightarrow$ past 365-day PO price $\rightarrow$ standard item master price $\rightarrow$ requester estimate for `NEW` items.
   - **Rate Contract Ceiling Tracking**: Tracks consumed ceiling dynamically, picking lowest-rate active contract with remaining headroom.
   - **Rule Priority Cascade**: `Capex Sourcing` $\rightarrow$ `Contract PO` $\rightarrow$ `Emergency PO` ($\le 5\text{L}$) $\rightarrow$ `Spot PO` ($< 2\text{L}$) $\rightarrow$ `RFQ` ($< 10\text{L}$) $\rightarrow$ `RFP` ($\ge 10\text{L}$).
   - **PO Consolidation**: Requirements sharing supplier, plant, and route within 24 hours are consolidated into single multi-line POs.
   - **Supplier Quarantine**: Blocked/Inactive suppliers (e.g. S004, S031) are strictly barred from POs or sourcing suggestions.
3. **Dynamic Policy Amendments (Blind-Test Ready)**:
   - Upload new policy text or PDF amendment.
   - In-app engine calculates plain-English diff preview.
   - 1-click Approval activates new version (e.g., v5.1) dynamically with **zero code modifications**.
4. **Automated Preferred Supplier Ranking**:
   - Calculates 548-day PO frequency, recency scoring, contract presence, on-time delivery %, and quality rating.
   - Sourcing suggestions top-up from active category suppliers sorted by operational reliability.
   - 1-click CSV Export (`item_code, rank, supplier_id, reference_price`).
5. **Buyer Workspace**:
   - Drilldown table of all requirements, applied policy clauses, and decision reasons.
   - 1-click Approval or Override with mandatory justification audit log.
6. **PDF Contract Ingestion**:
   - Automated parser for signed PDF contracts (`contracts/pdf/`) that start with zero consumed value.

---

## 🏗️ Architecture & Tech Stack

- **Backend**: FastAPI (Python 3.11), Pydantic v2, Pandas, RapidFuzz, PyPDF.
- **Frontend**: React + Vite + Tailwind CSS + Lucide Icons.
- **Rule Storage**: Versioned Declarative JSON schemas (`backend/policies/policy_v5_0.json`).
- **Containerization**: Docker & Docker Compose.

---

## 🚀 Quickstart (Local Run)

### Option 1: Docker Compose (Recommended)
```bash
docker compose up --build
```
- App UI: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### Option 2: Manual Local Setup

#### Backend:
```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install fastapi uvicorn pydantic python-multipart pandas pypdf python-dotenv rapidfuzz httpx

# 3. Start Backend Server
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Automated Test Suite (100% Pass Rate)

Run the full verification suite covering all 14 Worked Examples and the 186-line sample PR batch:

```bash
# Run unit tests verifying Worked Examples 1 through 14
python backend/tests/test_worked_examples.py

# Run Preferred Supplier Ranking test (Page 5 benchmarks)
python backend/tests/test_preferred_suppliers_service.py

# Run Fuzzy Matcher test (free-text abbreviations)
python backend/tests/test_fuzzy_matcher.py

# Run Full 186-line Batch test
python backend/tests/test_full_batch.py

# Run Blind Test Amendment Simulation (v5.0 -> v5.1)
python backend/tests/test_amendment_flow.py

# Run Full API Integration Suite
python backend/tests/test_api_endpoints.py
```

---

## 📊 Blind-Test Procedure (Thu 19 Nov)

1. **Run 1 (Baseline Policy v5.0)**:
   - Upload new test batch CSV via UI or `POST /api/process-batch`.
   - Click **Export Decisions** to download `yourname__run1.csv`.
2. **Run 2 (Policy Amendment)**:
   - Navigate to **Policy Manager** tab.
   - Upload the amendment PDF / paste text.
   - Review plain-language diff and click **Approve & Activate**.
   - Re-process the batch and download `yourname__run2.csv`.
3. **Preferred Supplier Export**:
   - Go to **Preferred Suppliers** tab.
   - Enter the target date specified by Cantill and click **Export CSV** to download `yourname__preferred.csv`.
4. **Push Outputs**:
   - Place all three CSVs in `submission/` folder:
     ```
     submission/
       ├── yourname__run1.csv
       ├── yourname__run2.csv
       └── yourname__preferred.csv
     ```
   - Commit and push before 12:00 noon IST.

---

## 📂 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (batch, policy, chat, suppliers, buyer)
│   │   ├── core/            # App configuration
│   │   ├── models/          # Pydantic schemas
│   │   ├── services/        # Policy Engine, Fuzzy Matcher, Preferred Supplier Service, etc.
│   │   └── main.py          # FastAPI application entrypoint
│   ├── policies/            # Versioned JSON policy definitions (v5.0, v5.1, etc.)
│   └── tests/               # Automated test suites for all policy worked examples
├── frontend/                # React Vite web interface
├── DECISIONS.md             # Business decisions, ranking formulas, edge cases
├── APPROACH.md              # Architecture, methodologies, and AI tooling disclosure
├── README.md                # Documentation and setup instructions
├── Dockerfile               # Production container definition
├── docker-compose.yml       # 1-command local runtime
└── .gitignore               # Strict exclusion of task data files
```
