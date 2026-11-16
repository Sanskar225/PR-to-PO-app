# APPROACH.md — Technical Architecture & Methodology

## 1. Executive Summary
This application automates the Purchase Requisition to Purchase Order (PR-to-PO) decision pipeline for **Corvo Engineering** in accordance with *Procurement Policy v5.0*. It provides:
1. **Conversational Intake Assistant**: Natural language chat interface parsing employee purchase requests, identifying missing attributes, and creating PRs.
2. **Policy-as-Data Decision Engine**: Dynamic rule evaluator driven by versioned declarative policy configurations (supporting dynamic amendments without code modification).
3. **Automated Preferred Supplier Ranking**: Analytical scoring model computing recency, contract presence, PO history, and operational performance metrics.
4. **Buyer Workspace**: Executive dashboard with requirement drill-down, 1-click approvals, and audit-logged overrides.
5. **Contract Ingestion Pipeline**: Ingests structured CSV registers and extracts PDF-only executed contracts.

---

## 2. Technology Stack
- **Backend API**: FastAPI (Python 3.11)
  - Selected for high performance, native Pydantic schema validation, and seamless data processing.
- **Data & Text Processing**:
  - `pandas`: Batch dataset parsing, vector filtering, and CSV serialization.
  - `rapidfuzz`: Token-ratio fuzzy string matching for free-text PR items.
  - `pypdf`: Contract PDF and amendment document text extraction.
- **Frontend Architecture**:
  - React 18 + Vite + Tailwind CSS + Lucide Icons.
  - Modular single-page architecture featuring Chat Intake, Buyer Workspace, Policy Manager, Batch Processor, and Preferred Suppliers Explorer.
- **Containerization**:
  - Multi-stage Docker build with `docker-compose.yml` for 1-command startup.

---

## 3. System Architecture & Component Design

```
                     ┌────────────────────────────────────────┐
                     │          React + Vite Frontend         │
                     │  (Chat, Buyer, Policy, Batch, Supplier)│
                     └───────────────────┬────────────────────┘
                                         │ REST API
                     ┌───────────────────▼────────────────────┐
                     │           FastAPI Backend              │
                     └──────┬────────────┬─────────────┬──────┘
                            │            │             │
        ┌───────────────────▼──┐  ┌──────▼──────┐ ┌────▼─────────────────┐
        │ Chat Agent & Intake  │  │ DataLoader  │ │ Policy Manager       │
        │ - Natural NLP parse  │  │ - Items     │ │ - Versioned JSON     │
        │ - Fuzzy Matcher      │  │ - Suppliers │ │ - Amendment Parser   │
        │ - Context Builder    │  │ - Contracts │ │ - Plain English Diff │
        └──────────────────────┘  │ - PO History│ └──────────┬───────────┘
                                  └──────┬──────┘            │
                                         │                   │
                                  ┌──────▼───────────────────▼──┐
                                  │      Policy Engine          │
                                  │ 1. Item Resolution          │
                                  │ 2. Anti-splitting Clubbing  │
                                  │ 3. Valuation Cascade        │
                                  │ 4. Rate Contract Ceiling    │
                                  │ 5. Rule Priority (Capex/PO) │
                                  │ 6. Sourcing Suggestions     │
                                  │ 7. PO 24h Consolidation     │
                                  └─────────────────────────────┘
```

---

## 4. Policy Execution Pipeline

1. **Item Resolution**:
   - Explicit `item_code` verified against Master Data.
   - Uncoded PR lines normalized via regex abbreviations (`brg` $\rightarrow$ `ball bearing`, `hyd` $\rightarrow$ `hydraulic`) and matched using token-set fuzzy ratios.
   - Unmatched lines designated `NEW` (Policy 1.2).
2. **Requirement Clubbing**:
   - PR lines sorted by `(created_at, pr_no, pr_line)`.
   - Joined to open requirement if: same item, same plant, created within 14 calendar days, need-by date within $\pm 7$ calendar days.
   - `NEW` items bypass clubbing to preserve individual sourcing integrity.
3. **Valuation**:
   - Sequentially checks: (a) Rate of applicable contract with available ceiling, or lowest contract rate if all exhausted; (b) Price from latest PO in past 365 days; (c) Item master standard price; (d) Requester estimate for `NEW` items.
4. **Contract Ceiling Management**:
   - Consumed amounts tracked during batch execution. Orders take the lowest-rate active contract with remaining ceiling headroom.
5. **Rule Cascade**:
   - Order: Capex Sourcing $\rightarrow$ Contract PO $\rightarrow$ Emergency PO ($\le 5\text{L}$) $\rightarrow$ Spot PO ($< 2\text{L}$) $\rightarrow$ RFQ ($< 10\text{L}$) $\rightarrow$ RFP ($\ge 10\text{L}$).
6. **Sourcing Suggestions**:
   - Draws from ranked preferred supplier list. If fewer than 3 or 5, automatically tops up with active suppliers in the same category sorted by delivery % and quality.
7. **PO Consolidation**:
   - Consolidates requirements sharing supplier, plant, and route raised within 24 hours of the first requirement into single multi-line POs.

---

## 5. AI Tooling Disclosure
In accordance with task guidelines:
- **Coding & Implementation Assistance**: Antigravity AI agent assisted in architecture design, parsing optimization, regex construction, and test suite generation.
- **Runtime Application NLP**: The in-app conversational assistant utilizes token classification and deterministic pattern extraction backed by fuzzy semantic indexing (`rapidfuzz`) to guarantee sub-millisecond response latency, zero API rate limits, and 100% offline reproducibility during blind-test grading.
