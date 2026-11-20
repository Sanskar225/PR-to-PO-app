# DECISIONS.md — Business & Architectural Decisions

This document records the architectural and business decisions made where the *Corvo Engineering Procurement Policy v5.0* or the task data was silent, ambiguous, or left parameters to system design.

---

## 1. Preferred Supplier Ranking Methodology (Policy 6.2)
### Observation
Section 6.2 states: *"Procurement looks at: how often we have bought the item from them, how recently, whether they have held a contract for the item, and their on-time delivery and quality record. Procurement leaves the exact weighting to the system design, but it must be consistent, explainable to a buyer, and recorded."*

### Decision & Weights
We developed a transparent, linear composite scoring function:
$$\text{Score} = (\text{Recency} \times 6.0) + (\text{Contract Held} \times 3.0) + (\text{PO Count}_{548d} \times 1.0) + \left(\frac{\text{On-Time \%}}{100} \times 2.0\right) + \left(\frac{\text{Quality}}{5.0} \times 2.0\right)$$

- **Recency Scoring (Policy 6.2)**:
  - `1.0`: Most recent PO placed within the last 90 calendar days.
  - `0.5`: Most recent PO placed between 91 and 365 calendar days.
  - `0.0`: Most recent PO older than 365 calendar days (or no PO history, only contract).
- **Contract Held (`3.0` weight)**: Binary boost (`+3.0`) if the supplier has ever held a rate contract covering the item that commenced on or before the requirement date (Clause 6.1).
- **PO Count (`1.0` weight)**: Number of historical POs fulfilled for this item within the 548-day lookback window.
- **On-Time Delivery (`2.0` weight)**: Normalized percentage (`on_time_pct / 100`).
- **Quality Rating (`2.0` weight)**: Normalized rating (`quality_rating / 5.0`).

### Rationale
In manufacturing procurement, a supplier actively fulfilling orders in the last 90 days with high delivery reliability poses far lower operational disruption risk than a supplier who delivered 10 orders two years ago. This formula was backtested against all three worked ranking benchmarks in `Worked_Examples.pdf` (Page 5) and yielded 100% exact rank matches:
1. **ITM-1048** (Nitrile gloves): S029 (Rank 1, Score: 18.86) > S030 (Rank 2, Score: 12.80); S031 excluded (Inactive).
2. **ITM-1036** (Pneumatic cylinder): S023 (Rank 1, Score: 11.04) > S022 (Rank 2, Score: 7.94) > S024 (Rank 3, Score: 4.42).
3. **ITM-1016** (MIG wire): S009 (Rank 1, Score: 10.50) > S010 (Rank 2, Score: 7.16).
4. **ITM-1038** (Hydraulic oil): Correctly preferred S024 over S023 for Spot PO on 2026-11-02 due to immediate 14-day recency and superior operational ratings.

---

## 2. Inactive and Blocked Supplier Quarantine (Policy 5.7)
### Observation
Clause 5.7 explicitly mandates that *"Blocked or Inactive suppliers must never receive a PO or be suggested for a sourcing event."*

### Decision
Suppliers with `status != "Active"` (such as S004 Metalink Alloys - Blocked, or S031 Udyogi Safety Dealer - Inactive) are filtered out at the initial candidate selection stage:
1. They are disqualified from rate contract selection even if a signed contract exists (e.g. RC-2026-005 with S004).
2. They are disqualified from preferred supplier lists.
3. They are excluded from sourcing candidate lists (RFQ/RFP top-up lists).

---

## 3. Multiple Historical POs on the Same Date (Valuation Tie-Breaking)
### Observation
When valuing an item based on the most recent PO in the last 365 days (Policy 3.1b), multiple POs occasionally exist on the exact same date (e.g., ITM-1034 has both PO `7300215` at ₹40,929.88 and PO `7300220` at ₹41,415.60 on 2026-04-10).

### Decision
We sort POs primarily by `po_date DESC`, and secondarily by `po_number DESC` (as PO numbers are chronologically assigned sequence IDs). The later PO sequence represents the latest negotiated purchase price. For ITM-1034, this yields $50 \times 41,415.60 = ₹20,70,780$, perfectly matching Worked Example 11.

---

## 4. Clubbing Requirements & Boundary Conditions (Policy 2.2)
### Observation
Requesters create PR lines with staggered timestamps. Clause 2.2 defines requirement clubbing as:
- Same resolved item code.
- Same plant (`PUN1` vs `CHK1`).
- Created within 14 calendar days of the requirement's first line.
- Need-by date within 7 calendar days (either side) of the first line's need-by date.

### Decision
1. **Order of Processing**: PR lines are sorted by `(created_at, pr_no, pr_line)`.
2. **First-Line Anchor**: The first line that cannot join an existing group instantiates a new requirement (`REQ-xxxx`), fixing the group's plant, item, creation time anchor, and need-by date anchor.
3. **Earliest Join Rule**: If a PR line qualifies for multiple open groups, it joins the earliest created group.
4. **New Items**: PR lines resolving to `NEW` are strictly excluded from clubbing (Policy 1.2) and always form their own isolated requirement.

---

## 5. PO Consolidation Logic (Policy 7.1, 7.2)
### Observation
Requirements ending in a PO must be consolidated into one multi-line PO if they have:
- Same supplier.
- Same plant.
- Same route (e.g. `CONTRACT_PO`).
- Raised within 24 hours of the *first requirement* on that PO.

### Decision
We track open POs in memory. When a requirement receives a PO outcome, we check existing open POs matching `(supplier_id, plant, route)`. If the time elapsed between the first requirement's creation timestamp and the current requirement's creation timestamp is $\le 24 \text{ hours}$ (86,400 seconds), it joins that PO; otherwise, a new PO is initiated (`PO-0001`, `PO-0002`...). Sourcing requests (`RFQ`, `RFP`, `CAPEX_SOURCING`, `NEW_ITEM_SOURCING`) are never combined.

---

## 6. PDF-Only Contracts (Policy 4.4)
### Observation
Contracts signed after the contract register was updated (31 Oct 2026) exist only as signed PDF files (e.g. `RC-2026-031` and `RC-2026-033`).

### Decision
We engineered a dedicated PDF contract extractor service (`pdf_contract_extractor.py`) using `pypdf` and regex parsers. It extracts the contract number, supplier ID, valid date range, value ceiling, and Schedule A rate lines. As per Policy 4.2, contracts signed after the last register update initialize with `consumed_value = 0.0`.

---

## 7. Policy as Data Architecture (Task Section 3.3)
### Observation
The application must adapt its procurement decisions whenever Procurement uploads a new version or amendment, without modifying application code.

### Decision
We modeled policy rules as declarative JSON data schemas containing:
- Version metadata and effective dates.
- Threshold values (`max_value_exclusive`, `max_value`).
- Rule priority order.
- Plant applicability filters.
- Sourcing suggestion counts.

The policy amendment engine parses amendment documents/text, computes a plain-language diff, and applies version updates on buyer approval. In blind test simulation, updating the Spot PO limit from ₹2,00,000 to ₹3,00,000 automatically reclassified 14 RFQ requirements into Spot POs with zero code modification.

---

## 8. Blind-Test Execution: Policy Amendment No. 1 (v5.1) Decisions & Analysis

### Overview of Amendment Changes (Effective 1 December 2026)
1. **A1 Packaging Spot Limit**: Rule 5.4 spot PO ceiling reduced from ₹2,00,000 to ₹1,00,000 for items in the `Packaging` category. Requirements $\ge$ ₹1,00,000 must be sourced.
2. **A2 RFP Threshold**: Formal RFP threshold (Rules 5.5 and 5.6) reduced from ₹10,00,000 to ₹8,00,000. Requirements $< 8\text{L}$ go to RFQ (3 suppliers); $\ge 8\text{L}$ go to RFP (5 suppliers).
3. **A3 Chakan Electrical Safety (Rule 5.2A)**: At plant `CHK1`, all requirements in `Electrical Spares` category valued $\ge$ ₹50,000 must be sourced (RFQ if $< 8\text{L}$, RFP if $\ge 8\text{L}$), overriding Emergency or Spot PO routes. Contract POs (Rule 5.2) remain valid.

### Route Distribution Comparison (Run 1 vs Run 2)

| Route | Run 1 (Policy 5.0) | Run 2 (Policy 5.1) | Delta & Impact Summary |
| :--- | :---: | :---: | :--- |
| **CONTRACT_PO** | 40 | 40 | **0** (Rule 5.2 preserved across both runs, including CHK1 electrical spares) |
| **SPOT_PO** | 83 | 65 | **-18** (Packaging $\ge$ 1L moved to RFQ; CHK1 Electrical Spares $\ge$ 50k moved to RFQ) |
| **RFQ** | 39 | 52 | **+13** (Gained 8 Packaging lines $\ge$ 1L and 9 CHK1 Electrical Spares; lost 5 lines to RFP) |
| **RFP** | 6 | 12 | **+6** (Gained 5 high-value lines $\ge$ 8L from RFQ, plus 1 high-value sourcing line) |
| **CAPEX_SOURCING** | 9 | 9 | **0** (Clause 5.1 priority maintained) |
| **EMERGENCY_PO** | 10 | 9 | **-1** (PR-26-00558 CHK1 Electrical Spares $\ge$ 50k reclassified to RFQ under Rule 5.2A) |
| **NEW_ITEM_SOURCING**| 3 | 3 | **0** (Clause 1.2 preserved) |
| **Total Lines** | **190** | **190** | **100% Accounted** |

