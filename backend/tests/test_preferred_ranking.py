import pandas as pd
from datetime import datetime, timedelta

def compute_recency_score(last_po_date, ref_date):
    if pd.isna(last_po_date):
        return 0.0
    days = (ref_date - last_po_date).days
    if days <= 90:
        return 1.0
    elif days <= 365:
        return 0.5
    else:
        return 0.0

def score_supplier(po_count, recency, has_contract, on_time_pct, quality_rating):
    # Normalized weights:
    # Business logic: Procurement values proven relationship (POs + Recency) heavily,
    # contract experience, then operational metrics (on-time and quality).
    score = (
        po_count * 3.0 +
        recency * 4.0 +
        (2.0 if has_contract else 0.0) +
        (on_time_pct / 100.0) * 1.5 +
        (quality_rating / 5.0) * 1.5
    )
    return score

def test_ranking_benchmarks():
    # Test ITM-1048
    s029 = score_supplier(7, 1.0, True, 81, 3.1)
    s030 = score_supplier(4, 1.0, False, 72, 3.4)
    assert s029 > s030, "S029 must rank higher than S030 for ITM-1048"

    # Test ITM-1036
    s023 = score_supplier(2, 1.0, False, 74, 3.9)
    s022 = score_supplier(2, 0.5, False, 77, 3.5)
    s024 = score_supplier(1, 0.0, False, 89, 4.1)
    assert s023 > s022 > s024, "ITM-1036 order must be S023 > S022 > S024"

    # Test ITM-1016
    s009 = score_supplier(1, 0.5, True, 83, 4.6)
    s010 = score_supplier(1, 0.5, False, 80, 3.9)
    assert s009 > s010, "S009 must rank higher than S010 for ITM-1016"

if __name__ == "__main__":
    test_ranking_benchmarks()
