from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Dict, Optional, Any
from app.domain.entities.supplier import Supplier

@dataclass
class RankedSupplier:
    item_code: str
    rank: int
    supplier_id: str
    supplier_name: str
    reference_price: float
    po_count_548d: int
    recency_score: float
    has_contract: bool
    on_time_pct: float
    quality_rating: float
    composite_score: float

class SupplierRankingDomainService:
    @staticmethod
    def compute_rankings(
        item_code: str,
        ref_date: date,
        active_suppliers: Dict[str, Supplier],
        po_history_entries: List[Any],
        contracts_covering_item: List[Any],
        weights: Dict[str, float],
        fallback_standard_price: float = 0.0
    ) -> List[RankedSupplier]:
        """
        Executes Policy Clauses 6.1, 6.2, 6.3:
        Calculates preferred supplier ranking as of ref_date.
        """
        date_548_ago = ref_date - timedelta(days=548)

        # 1. Gather PO statistics within 548 days
        supp_po_stats: Dict[str, Dict[str, Any]] = {}
        for po in po_history_entries:
            if po.item_code == item_code:
                # parse po_date if string
                p_date = po.po_date if isinstance(po.po_date, date) else date.fromisoformat(str(po.po_date)[:10])
                if date_548_ago <= p_date <= ref_date:
                    s_id = po.supplier_id
                    if s_id not in supp_po_stats:
                        supp_po_stats[s_id] = {
                            "po_count": 0,
                            "last_po_date": p_date,
                            "last_po_number": str(po.po_number),
                            "most_recent_price": po.unit_price
                        }
                    stat = supp_po_stats[s_id]
                    stat["po_count"] += 1
                    if (p_date > stat["last_po_date"]) or (p_date == stat["last_po_date"] and str(po.po_number) >= stat["last_po_number"]):
                        stat["last_po_date"] = p_date
                        stat["last_po_number"] = str(po.po_number)
                        stat["most_recent_price"] = po.unit_price

        # 2. Check contracts covering item that started on or before ref_date
        supp_contracts: Dict[str, Dict[str, Any]] = {}
        for c in contracts_covering_item:
            c_start = c.start_date if isinstance(c.start_date, date) else date.fromisoformat(str(c.start_date)[:10])
            if c_start <= ref_date:
                s_id = c.supplier_id
                rate = c.get_rate(item_code) if hasattr(c, "get_rate") else c.rates.get(item_code, 0.0)
                if s_id not in supp_contracts or c_start >= supp_contracts[s_id]["start_date"]:
                    supp_contracts[s_id] = {
                        "has_contract": True,
                        "rate": rate,
                        "start_date": c_start
                    }

        # 3. Candidate pool: Active suppliers with either PO in 548d or contract
        candidate_ids = set(supp_po_stats.keys()).union(set(supp_contracts.keys()))
        ranked_list: List[RankedSupplier] = []

        w_po = weights.get("po_count", 1.0)
        w_rec = weights.get("recency", 6.0)
        w_con = weights.get("contract", 3.0)
        w_ot = weights.get("on_time", 2.0)
        w_q = weights.get("quality", 2.0)

        for s_id in candidate_ids:
            supp = active_suppliers.get(s_id)
            if not supp or not supp.is_eligible:
                continue

            po_stat = supp_po_stats.get(s_id, {})
            po_count = po_stat.get("po_count", 0)
            last_date = po_stat.get("last_po_date")

            # Recency scoring: 1 = <=90d, 0.5 = <=365d, 0 = older
            recency = 0.0
            if last_date:
                days_diff = (ref_date - last_date).days
                if days_diff <= 90:
                    recency = 1.0
                elif days_diff <= 365:
                    recency = 0.5
                else:
                    recency = 0.0

            con_stat = supp_contracts.get(s_id, {})
            has_contract = con_stat.get("has_contract", False)

            # Reference price (Clause 6.3)
            if "most_recent_price" in po_stat:
                ref_price = po_stat["most_recent_price"]
            elif "rate" in con_stat:
                ref_price = con_stat["rate"]
            else:
                ref_price = fallback_standard_price

            on_time = supp.on_time_pct
            quality = supp.quality_rating

            score = (
                po_count * w_po +
                recency * w_rec +
                (w_con if has_contract else 0.0) +
                (on_time / 100.0) * w_ot +
                (quality / 5.0) * w_q
            )

            ranked_list.append(RankedSupplier(
                item_code=item_code,
                rank=0,
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

        ranked_list.sort(
            key=lambda x: (x.composite_score, x.on_time_pct, x.quality_rating),
            reverse=True
        )

        for i, s in enumerate(ranked_list):
            s.rank = i + 1

        return ranked_list

    @staticmethod
    def suggest_sourcing_candidates(
        item_code: str,
        needed_count: int,
        item_category: str,
        ranked_preferred: List[RankedSupplier],
        all_active_suppliers: List[Supplier]
    ) -> List[str]:
        """
        Policy Clause 6.4:
        Take preferred list in order. If fewer than needed (3 or 5), add other Active
        suppliers listing the category, best delivery and quality record first.
        """
        if item_code == "NEW":
            return []

        suggested = [r.supplier_id for r in ranked_preferred]

        if len(suggested) < needed_count:
            category_candidates = [
                s for s in all_active_suppliers
                if s.is_eligible and s.supplier_id not in suggested and s.serves_category(item_category)
            ]
            category_candidates.sort(
                key=lambda s: (s.on_time_pct, s.quality_rating),
                reverse=True
            )
            for supp in category_candidates:
                suggested.append(supp.supplier_id)
                if len(suggested) == needed_count:
                    break

        return suggested[:needed_count]
