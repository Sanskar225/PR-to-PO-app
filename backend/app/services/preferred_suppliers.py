from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
import pandas as pd
from app.models.schemas import PreferredSupplierRecord, Supplier, Contract, POHistoryEntry
from app.core.date_utils import parse_d

class PreferredSupplierService:
    def __init__(self, data_loader):
        self.data_loader = data_loader

    def get_preferred_suppliers_for_item(
        self,
        item_code: str,
        ref_date_str: str,
        ranking_weights: Optional[Dict[str, float]] = None
    ) -> List[PreferredSupplierRecord]:
        """
        Builds and ranks the preferred supplier list for an item as of ref_date_str (YYYY-MM-DD).
        Follows Policy Clause 6.1, 6.2, 6.3.
        """
        if ranking_weights is None:
            ranking_weights = {
                "po_count": 1.0,
                "recency": 6.0,
                "contract": 3.0,
                "on_time": 2.0,
                "quality": 2.0
            }

        ref_date = parse_d(ref_date_str)
        date_548_ago = ref_date - timedelta(days=548)

        # 1. Filter PO history for item in [date_548_ago, ref_date]
        item_pos = [
            po for po in self.data_loader.po_history
            if po.item_code == item_code
        ]
        
        # Supplier stats in 548 days
        # supplier_id -> { 'po_count': int, 'last_po_date': date, 'most_recent_price': float }
        supp_po_stats: Dict[str, Dict] = {}
        for po in item_pos:
            po_d = parse_d(po.po_date)
            if date_548_ago <= po_d <= ref_date:
                if po.supplier_id not in supp_po_stats:
                    supp_po_stats[po.supplier_id] = {
                        "po_count": 0,
                        "last_po_date": po_d,
                        "most_recent_price": po.unit_price
                    }
                s_stat = supp_po_stats[po.supplier_id]
                s_stat["po_count"] += 1
                if (po_d > s_stat["last_po_date"]) or (po_d == s_stat["last_po_date"] and str(po.po_number) >= str(s_stat.get("last_po_number", ""))):
                    s_stat["last_po_date"] = po_d
                    s_stat["last_po_number"] = po.po_number
                    s_stat["most_recent_price"] = po.unit_price

        # 2. Check contracts covering item that started on or before ref_date
        # supplier_id -> { 'has_contract': bool, 'most_recent_contract_rate': float, 'most_recent_start_date': date }
        supp_contracts: Dict[str, Dict] = {}
        for c_id, c in self.data_loader.contracts.items():
            if item_code in c.lines:
                c_start = parse_d(c.start_date)
                if c_start <= ref_date:
                    if c.supplier_id not in supp_contracts:
                        supp_contracts[c.supplier_id] = {
                            "has_contract": True,
                            "rate": c.lines[item_code],
                            "start_date": c_start
                        }
                    else:
                        if c_start >= supp_contracts[c.supplier_id]["start_date"]:
                            supp_contracts[c.supplier_id] = {
                                "has_contract": True,
                                "rate": c.lines[item_code],
                                "start_date": c_start
                            }

        # 3. Form candidate list: Active suppliers with either (a) PO in 548d or (b) contract started on/before ref_date
        candidate_ids = set(supp_po_stats.keys()).union(set(supp_contracts.keys()))
        candidates: List[PreferredSupplierRecord] = []

        for s_id in candidate_ids:
            supp = self.data_loader.suppliers.get(s_id)
            if not supp or supp.status != "Active":
                # Clause 5.7 / 6.1: Blocked or Inactive suppliers are excluded
                continue

            po_stat = supp_po_stats.get(s_id, {})
            po_count = po_stat.get("po_count", 0)
            last_po_date = po_stat.get("last_po_date", None)
            
            # Recency: 1 = last PO within 90 days, 0.5 = within a year (365d), 0 = older
            recency = 0.0
            if last_po_date:
                days_diff = (ref_date - last_po_date).days
                if days_diff <= 90:
                    recency = 1.0
                elif days_diff <= 365:
                    recency = 0.5
                else:
                    recency = 0.0

            contract_stat = supp_contracts.get(s_id, {})
            has_contract = contract_stat.get("has_contract", False)

            # Reference price (Clause 6.3):
            # price on most recent PO in 548d; if none, rate in most recent contract
            if "most_recent_price" in po_stat:
                ref_price = po_stat["most_recent_price"]
            elif "rate" in contract_stat:
                ref_price = contract_stat["rate"]
            else:
                # fallback to standard price
                item = self.data_loader.items.get(item_code)
                ref_price = item.standard_price if item else 0.0

            on_time = supp.on_time_pct
            quality = supp.quality_rating

            # Composite score calculation
            score = (
                po_count * ranking_weights.get("po_count", 3.0) +
                recency * ranking_weights.get("recency", 4.0) +
                (ranking_weights.get("contract", 2.0) if has_contract else 0.0) +
                (on_time / 100.0) * ranking_weights.get("on_time", 1.5) +
                (quality / 5.0) * ranking_weights.get("quality", 1.5)
            )

            candidates.append(PreferredSupplierRecord(
                item_code=item_code,
                rank=0, # will set after sorting
                supplier_id=s_id,
                supplier_name=supp.name,
                reference_price=round(ref_price, 2),
                po_count_548d=po_count,
                recency_score=recency,
                has_contract=has_contract,
                on_time_pct=on_time,
                quality_rating=quality,
                composite_score=round(score, 3)
            ))

        # Sort descending by composite score, then on-time, then quality
        candidates.sort(
            key=lambda x: (x.composite_score, x.on_time_pct, x.quality_rating),
            reverse=True
        )

        for i, c in enumerate(candidates):
            c.rank = i + 1

        return candidates

    def get_first_preferred_supplier(self, item_code: str, ref_date_str: str) -> Optional[PreferredSupplierRecord]:
        ranked = self.get_preferred_suppliers_for_item(item_code, ref_date_str)
        return ranked[0] if ranked else None

    def suggest_suppliers_for_sourcing(
        self,
        item_code: str,
        needed_count: int,
        ref_date_str: str
    ) -> List[str]:
        """
        Clause 6.4:
        Take preferred list in order. If fewer suppliers than needed (3 or 5),
        add other Active suppliers that list item's category in supplier master,
        best delivery and quality record first. New items get no suggestions.
        """
        if item_code == "NEW":
            return []

        item = self.data_loader.items.get(item_code)
        if not item:
            return []

        ranked_pref = self.get_preferred_suppliers_for_item(item_code, ref_date_str)
        suggested: List[str] = [p.supplier_id for p in ranked_pref]

        if len(suggested) < needed_count:
            # Top up from active suppliers in same category
            cat = item.category
            category_candidates = []
            for s_id, supp in self.data_loader.suppliers.items():
                if supp.status == "Active" and s_id not in suggested:
                    # check if supp has cat in its categories
                    if any(cat.lower() == c.lower() for c in supp.categories):
                        category_candidates.append(supp)

            # Sort best delivery and quality record first: on_time_pct, quality_rating
            category_candidates.sort(
                key=lambda s: (s.on_time_pct, s.quality_rating),
                reverse=True
            )

            for supp in category_candidates:
                suggested.append(supp.supplier_id)
                if len(suggested) == needed_count:
                    break

        return suggested[:needed_count]

    def export_preferred_suppliers_csv(self, ref_date_str: str, top_k: int = 3) -> str:
        """
        Brief Section 3.5:
        Export it as CSV (item_code, rank, supplier_id, reference_price, top 3) as of a chosen date.
        """
        rows = []
        for item_code in sorted(self.data_loader.items.keys()):
            ranked = self.get_preferred_suppliers_for_item(item_code, ref_date_str)
            for r in ranked[:top_k]:
                rows.append({
                    "item_code": r.item_code,
                    "rank": r.rank,
                    "supplier_id": r.supplier_id,
                    "reference_price": r.reference_price
                })
        df = pd.DataFrame(rows)
        return df.to_csv(index=False)
