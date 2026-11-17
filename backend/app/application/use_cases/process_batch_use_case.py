import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any

from app.domain.entities.pr_line import PurchaseRequisitionLine, UrgencyLevel
from app.domain.entities.requirement import RequirementGroup
from app.domain.entities.contract import RateContract
from app.domain.policies.specification import EvaluationContext
from app.domain.services.clubbing_service import ClubbingDomainService
from app.domain.services.valuation_service import ValuationDomainService
from app.domain.services.supplier_ranking_service import SupplierRankingDomainService
from app.domain.services.consolidation_service import ConsolidationDomainService
from app.domain.repositories.interfaces import (
    IItemRepository, ISupplierRepository, IContractRepository,
    IPOHistoryRepository, IRequirementRepository, IPolicyRepository
)
from app.infrastructure.matching.rapidfuzz_matcher import RapidFuzzItemMatcher
from app.application.dto.schemas import PRLineDTO, DecisionOutputDTO, BatchProcessResultDTO

class ProcessBatchUseCase:
    def __init__(
        self,
        item_repo: IItemRepository,
        supplier_repo: ISupplierRepository,
        contract_repo: IContractRepository,
        po_history_repo: IPOHistoryRepository,
        requirement_repo: IRequirementRepository,
        policy_repo: IPolicyRepository
    ):
        self.item_repo = item_repo
        self.supplier_repo = supplier_repo
        self.contract_repo = contract_repo
        self.po_history_repo = po_history_repo
        self.requirement_repo = requirement_repo
        self.policy_repo = policy_repo

    def execute(self, pr_dtos: List[PRLineDTO], filename: str = "batch.csv") -> BatchProcessResultDTO:
        batch_id = f"BATCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        active_policy = self.policy_repo.get_active_policy()
        items_map = self.item_repo.get_all_indexed()
        active_suppliers_map = {s.supplier_id: s for s in self.supplier_repo.get_all_active()}
        all_active_suppliers_list = self.supplier_repo.get_all_active()
        all_contracts = self.contract_repo.get_all()
        all_po_history = self.po_history_repo.get_all()

        matcher = RapidFuzzItemMatcher(items_map)

        # 1. Convert DTOs to Domain PR lines with item resolution
        domain_lines: List[PurchaseRequisitionLine] = []
        for dto in pr_dtos:
            resolved_code, score = matcher.resolve_item(dto.item_code, dto.description)
            created_dt = datetime.strptime(dto.created_at[:16], "%Y-%m-%d %H:%M")
            need_by = date.fromisoformat(dto.need_by_date[:10])
            urgency = UrgencyLevel.from_str(dto.urgency)

            domain_lines.append(PurchaseRequisitionLine(
                pr_no=dto.pr_no,
                pr_line=dto.pr_line,
                created_at=created_dt,
                requester=dto.requester,
                department=dto.department,
                plant=dto.plant,
                item_code=dto.item_code,
                description=dto.description,
                quantity=dto.quantity,
                uom=dto.uom,
                estimated_unit_price=dto.estimated_unit_price,
                need_by_date=need_by,
                urgency=urgency,
                resolved_item_code=resolved_code
            ))

        # 2. Domain Clubbing (Anti-Splitting Invariants - Clause 2.1, 2.2)
        clubbed_groups = ClubbingDomainService.club_pr_lines(
            domain_lines,
            creation_window_days=active_policy.clubbing_creation_window_days,
            need_by_window_days=active_policy.clubbing_need_by_window_days
        )

        # 3. Evaluate each RequirementGroup
        # Maintain local contract ceiling tracking for this run
        # Policy Clause 4.1: Contract applies only if supplier is Active!
        eligible_contracts = [
            c for c in all_contracts
            if active_suppliers_map.get(c.supplier_id) and active_suppliers_map.get(c.supplier_id).is_eligible
        ]

        for req in clubbed_groups:
            self._evaluate_requirement_group(
                req=req,
                policy=active_policy,
                items_map=items_map,
                active_suppliers=active_suppliers_map,
                all_active_suppliers_list=all_active_suppliers_list,
                contracts=eligible_contracts,
                po_history=all_po_history
            )

        # 4. Domain PO Consolidation (Clause 7.1, 7.2)
        ConsolidationDomainService.consolidate_purchase_orders(
            requirements=clubbed_groups,
            window_hours=active_policy.consolidation_window_hours
        )

        # 5. Persist through Requirement Repository
        self.requirement_repo.save_batch_results(
            batch_id=batch_id,
            filename=filename,
            requirements=clubbed_groups
        )

        # 6. Map to flat DecisionOutputDTOs in original PR sequence
        line_to_group: Dict[Tuple[str, int], RequirementGroup] = {}
        for g in clubbed_groups:
            for l in g.lines:
                line_to_group[(l.pr_no, l.pr_line)] = g

        output_decisions: List[DecisionOutputDTO] = []
        for l in domain_lines:
            target_group = line_to_group[(l.pr_no, l.pr_line)]
            output_decisions.append(DecisionOutputDTO(
                pr_no=l.pr_no,
                pr_line=l.pr_line,
                resolved_item_code=target_group.resolved_item_code,
                group_id=target_group.group_id,
                po_id=target_group.po_id,
                decision=target_group.decision or "PO",
                route=target_group.route or "SPOT_PO",
                supplier_id=target_group.supplier_id,
                unit_price=round(target_group.unit_price, 2) if target_group.unit_price is not None else None,
                group_value_inr=round(target_group.group_value_inr, 2),
                suggested_supplier_ids=target_group.suggested_supplier_ids,
                policy_version=target_group.policy_version,
                reason=target_group.reason
            ))

        # Metrics
        route_dist: Dict[str, int] = {}
        total_val = 0.0
        po_ids = set()
        for d in output_decisions:
            route_dist[d.route] = route_dist.get(d.route, 0) + 1
            total_val += d.group_value_inr
            if d.po_id:
                po_ids.add(d.po_id)

        return BatchProcessResultDTO(
            batch_id=batch_id,
            filename=filename,
            total_lines=len(output_decisions),
            unique_requirements=len(clubbed_groups),
            consolidated_pos=len(po_ids),
            total_value_inr=round(total_val, 2),
            route_distribution=route_dist,
            policy_version_applied=active_policy.version,
            decisions=output_decisions
        )

    def _evaluate_requirement_group(
        self,
        req: RequirementGroup,
        policy: Any,
        items_map: Dict[str, Any],
        active_suppliers: Dict[str, Any],
        all_active_suppliers_list: List[Any],
        contracts: List[RateContract],
        po_history: List[Any]
    ) -> None:
        item_code = req.resolved_item_code
        req_date = req.requirement_date
        item_master_item = items_map.get(item_code)

        # 1. Handle NEW item (Clause 1.2)
        if item_code == "NEW":
            est_price = req.first_pr.estimated_unit_price or 0.0
            req.decision = "SOURCING_REQUEST"
            req.route = "NEW_ITEM_SOURCING"
            req.unit_price = None
            req.group_value_inr = req.total_quantity * est_price
            req.supplier_id = None
            req.suggested_supplier_ids = None
            req.policy_version = policy.version
            req.reason = "Policy clause 1.2: New item not in item master goes to sourcing; valued at requester's estimate"
            return

        # 2. Gather 365d PO history for valuation
        date_365_ago = req_date - timedelta(days=365)
        pos_365d = [
            po for po in po_history
            if po.item_code == item_code and date_365_ago <= (po.po_date if isinstance(po.po_date, date) else date.fromisoformat(str(po.po_date)[:10])) <= req_date
        ]

        # 3. Check if bought from an Active supplier in last 365 days
        bought_in_last_365_active = any(
            active_suppliers.get(po.supplier_id) and active_suppliers.get(po.supplier_id).is_eligible
            for po in pos_365d
        )

        # 4. Valuation Cascade (Clause 3.1)
        val_result = ValuationDomainService.value_requirement(
            requirement=req,
            available_contracts=contracts,
            recent_pos_365d=pos_365d,
            standard_price=item_master_item.standard_price if item_master_item else 0.0
        )
        req.group_value_inr = val_result.total_value

        # 5. Preferred supplier ranking (Clause 6.1, 6.2, 6.3)
        contracts_covering = [c for c in contracts if c.covers_item(item_code)]
        ranked_pref = SupplierRankingDomainService.compute_rankings(
            item_code=item_code,
            ref_date=req_date,
            active_suppliers=active_suppliers,
            po_history_entries=po_history,
            contracts_covering_item=contracts_covering,
            weights=policy.ranking_weights,
            fallback_standard_price=item_master_item.standard_price if item_master_item else 0.0
        )
        first_pref = ranked_pref[0] if ranked_pref else None

        # Build EvaluationContext for Specification Pattern
        context = EvaluationContext(
            item_master_item=item_master_item,
            has_valid_contract=(val_result.selected_contract is not None),
            selected_contract=val_result.selected_contract,
            selected_contract_rate=val_result.selected_contract_rate,
            bought_in_last_365_days=bought_in_last_365_active,
            requirement_value=req.group_value_inr,
            first_preferred_supplier=first_pref
        )

        # 6. Evaluate Policy Rules in Priority Order (Clause 5.1 to 5.6)
        matched_rule = None
        for rule in policy.rules:
            if rule.specification.is_satisfied_by(req, context):
                matched_rule = rule
                break

        if not matched_rule:
            # Fallback to RFP if above all limits
            req.decision = "SOURCING_REQUEST"
            req.route = "RFP"
            suggested = SupplierRankingDomainService.suggest_sourcing_candidates(
                item_code, 5, item_master_item.category if item_master_item else "",
                ranked_pref, all_active_suppliers_list
            )
            req.suggested_supplier_ids = ";".join(suggested) if suggested else None
            req.policy_version = policy.version
            req.reason = "Policy clause 5.6: Formal RFP sourcing; suggested 5 suppliers"
            return

        req.decision = matched_rule.outcome
        req.route = matched_rule.route
        req.policy_version = policy.version

        # Populate Route Specific Details
        if matched_rule.route == "CONTRACT_PO":
            # Consume ceiling invariant
            val_result.selected_contract.consume_ceiling(req.group_value_inr)
            req.supplier_id = val_result.selected_contract.supplier_id
            req.unit_price = val_result.selected_contract_rate
            req.suggested_supplier_ids = None
            req.reason = f"Policy clause 5.2: Rate contract {val_result.selected_contract.contract_id} active with available ceiling"

        elif matched_rule.route in ["EMERGENCY_PO", "SPOT_PO"]:
            req.supplier_id = first_pref.supplier_id
            req.unit_price = first_pref.reference_price
            req.suggested_supplier_ids = None
            clause = "5.3" if matched_rule.route == "EMERGENCY_PO" else "5.4"
            req.reason = f"Policy clause {clause}: {matched_rule.name} to 1st preferred supplier {first_pref.supplier_id} at reference price ₹{first_pref.reference_price:,.2f}"

        elif matched_rule.route in ["CAPEX_SOURCING", "RFQ", "RFP"]:
            count = matched_rule.suggest_count or (3 if matched_rule.route == "RFQ" else 5)
            suggested = SupplierRankingDomainService.suggest_sourcing_candidates(
                item_code, count, item_master_item.category if item_master_item else "",
                ranked_pref, all_active_suppliers_list
            )
            req.supplier_id = None
            req.unit_price = None
            req.suggested_supplier_ids = ";".join(suggested) if suggested else None
            req.reason = f"Policy clause {matched_rule.clause}: {matched_rule.name} ({'capex' if matched_rule.route == 'CAPEX_SOURCING' else 'quotes needed'}); suggested {len(suggested)} suppliers"
