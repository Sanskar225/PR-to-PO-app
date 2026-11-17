import io
import csv
from datetime import date
from typing import Dict, List, Optional
from app.domain.repositories.interfaces import (
    IItemRepository, ISupplierRepository, IContractRepository,
    IPOHistoryRepository, IPolicyRepository
)
from app.domain.services.supplier_ranking_service import (
    SupplierRankingDomainService, RankedSupplier
)

class RankPreferredSuppliersUseCase:
    def __init__(
        self,
        item_repo: IItemRepository,
        supplier_repo: ISupplierRepository,
        contract_repo: IContractRepository,
        po_history_repo: IPOHistoryRepository,
        policy_repo: IPolicyRepository
    ):
        self.item_repo = item_repo
        self.supplier_repo = supplier_repo
        self.contract_repo = contract_repo
        self.po_history_repo = po_history_repo
        self.policy_repo = policy_repo

    def get_rankings(
        self,
        ref_date: date,
        item_code: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, List[RankedSupplier]]:
        policy = self.policy_repo.get_active_policy()
        items = self.item_repo.get_all_indexed()
        active_suppliers = {s.supplier_id: s for s in self.supplier_repo.get_all_active()}
        contracts = self.contract_repo.get_all()
        po_history = self.po_history_repo.get_all()

        target_codes = [item_code] if item_code and item_code in items else sorted(items.keys())
        results: Dict[str, List[RankedSupplier]] = {}

        for code in target_codes:
            item = items.get(code)
            covering_contracts = [c for c in contracts if c.covers_item(code)]
            ranked = SupplierRankingDomainService.compute_rankings(
                item_code=code,
                ref_date=ref_date,
                active_suppliers=active_suppliers,
                po_history_entries=po_history,
                contracts_covering_item=covering_contracts,
                weights=policy.ranking_weights,
                fallback_standard_price=item.standard_price if item else 0.0
            )
            results[code] = ranked[:top_k]

        return results

    def export_csv(self, ref_date: date, top_k: int = 3) -> str:
        """
        Task Brief Section 3.5:
        Export as CSV (item_code, rank, supplier_id, reference_price, top 3) as of a chosen date.
        """
        rankings = self.get_rankings(ref_date=ref_date, top_k=top_k)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["item_code", "rank", "supplier_id", "reference_price"])

        for code in sorted(rankings.keys()):
            for r in rankings[code]:
                writer.writerow([r.item_code, r.rank, r.supplier_id, r.reference_price])

        return output.getvalue()
