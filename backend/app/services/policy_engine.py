from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any
import copy
from app.models.schemas import (
    PRLineInput, DecisionRecord, PolicyDocument, Item, Supplier, Contract, POHistoryEntry
)
from app.services.data_loader import DataLoader
from app.services.fuzzy_matcher import FuzzyMatcher
from app.services.preferred_suppliers import PreferredSupplierService

class RequirementGroupInternal:
    def __init__(self, group_id: str, first_pr: PRLineInput, resolved_item_code: str):
        self.group_id = group_id
        self.resolved_item_code = resolved_item_code
        self.plant = first_pr.plant
        self.first_pr_line = first_pr
        self.pr_lines: List[PRLineInput] = [first_pr]
        
        # Parsed dates
        self.first_created_dt = datetime.strptime(first_pr.created_at, "%Y-%m-%d %H:%M")
        self.req_date_str = self.first_created_dt.strftime("%Y-%m-%d")
        self.first_need_by_dt = datetime.strptime(first_pr.need_by_date[:10], "%Y-%m-%d").date()

    @property
    def total_quantity(self) -> float:
        return sum(line.quantity for line in self.pr_lines)

    @property
    def is_emergency(self) -> bool:
        return any(line.urgency.strip().lower() == "emergency" for line in self.pr_lines)

    def can_join(self, pr: PRLineInput, resolved_code: str, window_days: int = 14, need_by_days: int = 7) -> bool:
        if resolved_code == "NEW":
            return False  # Rule 1.2: NEW item never clubbed
        if self.resolved_item_code != resolved_code:
            return False
        if self.plant != pr.plant:
            return False
            
        pr_dt = datetime.strptime(pr.created_at, "%Y-%m-%d %H:%M")
        if (pr_dt - self.first_created_dt).total_seconds() > (window_days * 86400):
            return False
        if pr_dt < self.first_created_dt:
            return False
            
        pr_need_by = datetime.strptime(pr.need_by_date[:10], "%Y-%m-%d").date()
        if abs((pr_need_by - self.first_need_by_dt).days) > need_by_days:
            return False
            
        return True

    def add_line(self, pr: PRLineInput):
        self.pr_lines.append(pr)


class PolicyEngine:
    def __init__(self, data_loader: DataLoader, policy: PolicyDocument):
        self.data_loader = data_loader
        self.policy = policy
        self.fuzzy_matcher = FuzzyMatcher(data_loader.items)
        self.preferred_service = PreferredSupplierService(data_loader)

    def process_pr_batch(self, pr_lines: List[PRLineInput]) -> List[DecisionRecord]:
        """
        Executes policy decisions for a batch of PR lines.
        Returns a list of DecisionRecord, exactly one row per PR line.
        """
        # Step 0: Clone contracts so ceiling consumption is tracked in-memory for this run
        contracts_state = copy.deepcopy(self.data_loader.contracts)

        # Step 1: Resolve items & sort PR lines in order of creation time (then PR number, then line number)
        # Policy Clause 2.2
        annotated_prs = []
        for pr in pr_lines:
            resolved_code, score = self.fuzzy_matcher.match(pr.item_code, pr.description)
            annotated_prs.append({
                "pr": pr,
                "resolved_item_code": resolved_code,
                "created_dt": datetime.strptime(pr.created_at, "%Y-%m-%d %H:%M")
            })

        annotated_prs.sort(key=lambda x: (x["created_dt"], x["pr"].pr_no, x["pr"].pr_line))

        # Step 2: Clubbing into requirements (Clause 2.1, 2.2)
        club_window_days = self.policy.clubbing_rules.get("creation_window_days", 14)
        need_by_window_days = self.policy.clubbing_rules.get("need_by_window_days", 7)
        groups: List[RequirementGroupInternal] = []
        group_counter = 1

        for item in annotated_prs:
            pr = item["pr"]
            code = item["resolved_item_code"]
            joined = False

            if code != "NEW":
                for g in groups:
                    if g.can_join(pr, code, club_window_days, need_by_window_days):
                        g.add_line(pr)
                        joined = True
                        break

            if not joined:
                gid = f"REQ-{group_counter:04d}"
                group_counter += 1
                new_group = RequirementGroupInternal(gid, pr, code)
                groups.append(new_group)

        # Step 3, 4, 5: Value each requirement, check contracts, apply policy decision rules
        # Requirements are processed in order of requirement date (Clause 4.2)
        groups.sort(key=lambda g: g.first_created_dt)

        requirement_decisions: Dict[str, Dict[str, Any]] = {}

        for g in groups:
            dec = self._evaluate_requirement(g, contracts_state)
            requirement_decisions[g.group_id] = dec

        # Step 7: Consolidate POs (Clause 7.1, 7.2)
        # Combine requirements that end in a PO if:
        # same supplier, same plant, same route, raised within 24h of first requirement on that PO
        open_pos: List[Dict[str, Any]] = [] # list of { po_id, supplier_id, plant, route, first_created_dt }
        po_counter = 1

        # Process requirements in order of creation time
        for g in groups:
            dec = requirement_decisions[g.group_id]
            if dec["decision"] == "PO":
                supp_id = dec["supplier_id"]
                plant = g.plant
                route = dec["route"]
                req_dt = g.first_created_dt
                
                assigned_po = None
                window_hours = self.policy.consolidation_window_hours
                for po in open_pos:
                    if (po["supplier_id"] == supp_id and 
                        po["plant"] == plant and 
                        po["route"] == route):
                        diff_seconds = (req_dt - po["first_created_dt"]).total_seconds()
                        if 0 <= diff_seconds <= (window_hours * 3600):
                            assigned_po = po["po_id"]
                            break
                            
                if not assigned_po:
                    assigned_po = f"PO-{po_counter:04d}"
                    po_counter += 1
                    open_pos.append({
                        "po_id": assigned_po,
                        "supplier_id": supp_id,
                        "plant": plant,
                        "route": route,
                        "first_created_dt": req_dt
                    })
                    
                dec["po_id"] = assigned_po
            else:
                dec["po_id"] = None

        # Build final flat records in original PR batch order
        output_records: List[DecisionRecord] = []
        for item in annotated_prs:
            pr = item["pr"]
            code = item["resolved_item_code"]
            # Find which group this PR belongs to
            target_group = None
            for g in groups:
                if any(p.pr_no == pr.pr_no and p.pr_line == pr.pr_line for p in g.pr_lines):
                    target_group = g
                    break
                    
            dec = requirement_decisions[target_group.group_id]
            
            output_records.append(DecisionRecord(
                pr_no=pr.pr_no,
                pr_line=pr.pr_line,
                resolved_item_code=code,
                group_id=target_group.group_id,
                po_id=dec.get("po_id"),
                decision=dec["decision"],
                route=dec["route"],
                supplier_id=dec.get("supplier_id"),
                unit_price=round(dec["unit_price"], 2) if dec.get("unit_price") is not None else None,
                group_value_inr=round(dec["group_value_inr"], 2),
                suggested_supplier_ids=dec.get("suggested_supplier_ids"),
                policy_version=self.policy.version,
                reason=dec["reason"]
            ))

        return output_records

    def _evaluate_requirement(
        self,
        group: RequirementGroupInternal,
        contracts_state: Dict[str, Contract]
    ) -> Dict[str, Any]:
        """
        Evaluates a single requirement according to Policy v5.0.
        """
        item_code = group.resolved_item_code
        req_date = group.req_date_str
        req_date_obj = datetime.strptime(req_date, "%Y-%m-%d").date()
        total_qty = group.total_quantity

        # Case 1: NEW item (Policy 1.2)
        if item_code == "NEW":
            est_price = group.first_pr_line.estimated_unit_price or 0.0
            val = total_qty * est_price
            return {
                "decision": "SOURCING_REQUEST",
                "route": "NEW_ITEM_SOURCING",
                "supplier_id": None,
                "unit_price": None,
                "group_value_inr": val,
                "suggested_supplier_ids": None,
                "reason": "Policy clause 1.2: New item not in item master goes to sourcing; valued at requester's estimate"
            }

        item_master_item = self.data_loader.items.get(item_code)

        # Case 2: Check applicable contracts (Clause 4.1, 4.2, 4.3)
        # Contract applies if:
        # covers item, req_date between start and end (inclusive), supplier Active
        applicable_contracts: List[Tuple[Contract, float]] = [] # (contract, rate)
        for c_id, c in contracts_state.items():
            if item_code in c.lines:
                supp = self.data_loader.suppliers.get(c.supplier_id)
                if supp and supp.status == "Active":
                    c_start = datetime.strptime(c.start_date[:10], "%Y-%m-%d").date()
                    c_end = datetime.strptime(c.end_date[:10], "%Y-%m-%d").date()
                    if c_start <= req_date_obj <= c_end:
                        rate = c.lines[item_code]
                        applicable_contracts.append((c, rate))

        # Sort contracts by rate ascending (lowest rate first - Clause 4.3)
        applicable_contracts.sort(key=lambda x: x[1])

        # Step 3: Valuing requirement (Clause 3.1)
        # Unit price is first of:
        # (a) rate of contract that will be used, or if every applicable contract is out of ceiling, lowest applicable contract rate;
        # (b) price on most recent PO for the item in 365 days before requirement date;
        # (c) item master standard price.
        selected_contract = None
        selected_contract_rate = None
        lowest_applicable_contract_rate = applicable_contracts[0][1] if applicable_contracts else None

        for c, rate in applicable_contracts:
            req_val = total_qty * rate
            if (c.consumed_value + req_val) <= c.value_cap:
                selected_contract = c
                selected_contract_rate = rate
                break

        valuation_unit_price = None
        valuation_source = ""

        if selected_contract_rate is not None:
            valuation_unit_price = selected_contract_rate
            valuation_source = f"contract {selected_contract.contract_id} rate"
        elif lowest_applicable_contract_rate is not None:
            valuation_unit_price = lowest_applicable_contract_rate
            valuation_source = f"lowest contract rate (ceiling exhausted)"
        else:
            # Check most recent PO in last 365 days
            date_365_ago = req_date_obj - timedelta(days=365)
            recent_pos = [
                po for po in self.data_loader.po_history
                if po.item_code == item_code and date_365_ago <= datetime.strptime(po.po_date[:10], "%Y-%m-%d").date() <= req_date_obj
            ]
            if recent_pos:
                # sort by date and po_number descending to pick the latest PO
                recent_pos.sort(key=lambda p: (p.po_date, p.po_number), reverse=True)
                valuation_unit_price = recent_pos[0].unit_price
                valuation_source = f"recent PO {recent_pos[0].po_number} price"
            else:
                valuation_unit_price = item_master_item.standard_price if item_master_item else 0.0
                valuation_source = "item master standard price"

        req_value = total_qty * valuation_unit_price

        # Check if item was bought from an Active supplier in last 365 days
        date_365_ago = req_date_obj - timedelta(days=365)
        bought_in_last_365_active = any(
            po.item_code == item_code and
            date_365_ago <= datetime.strptime(po.po_date[:10], "%Y-%m-%d").date() <= req_date_obj and
            self.data_loader.suppliers.get(po.supplier_id) and
            self.data_loader.suppliers.get(po.supplier_id).status == "Active"
            for po in self.data_loader.po_history
        )

        # Check Capex (Rule 5.1)
        if item_master_item and item_master_item.item_type.lower() == "capex":
            suggested = self.preferred_service.suggest_suppliers_for_sourcing(item_code, 5, req_date)
            return {
                "decision": "SOURCING_REQUEST",
                "route": "CAPEX_SOURCING",
                "supplier_id": None,
                "unit_price": None,
                "group_value_inr": req_value,
                "suggested_supplier_ids": ";".join(suggested) if suggested else None,
                "reason": f"Policy clause 5.1: Capex item requires sourcing; suggested {len(suggested)} suppliers"
            }

        # Check Contract PO (Rule 5.2)
        if selected_contract is not None:
            # Consume ceiling!
            selected_contract.consumed_value += req_value
            return {
                "decision": "PO",
                "route": "CONTRACT_PO",
                "supplier_id": selected_contract.supplier_id,
                "unit_price": selected_contract_rate,
                "group_value_inr": req_value,
                "suggested_supplier_ids": None,
                "reason": f"Policy clause 5.2: Rate contract {selected_contract.contract_id} active with available ceiling"
            }

        # Check Emergency PO (Rule 5.3)
        # Emergency, value <= 5,00,000, bought from Active supplier in last 365 days
        if group.is_emergency and req_value <= 500000.0 and bought_in_last_365_active:
            pref = self.preferred_service.get_first_preferred_supplier(item_code, req_date)
            if pref:
                return {
                    "decision": "PO",
                    "route": "EMERGENCY_PO",
                    "supplier_id": pref.supplier_id,
                    "unit_price": pref.reference_price,
                    "group_value_inr": req_value,
                    "suggested_supplier_ids": None,
                    "reason": f"Policy clause 5.3: Emergency PO (value <= 5L, purchase history in 365d) to 1st preferred supplier {pref.supplier_id}"
                }

        # Check Spot PO (Rule 5.4)
        # Value < 2,00,000, bought from Active supplier in last 365 days
        # (Check active policy threshold for spot limit)
        spot_limit = 200000.0
        for r in self.policy.rules:
            if r.route == "SPOT_PO":
                spot_limit = r.condition.get("max_value_exclusive", 200000.0)

        if req_value < spot_limit and bought_in_last_365_active:
            pref = self.preferred_service.get_first_preferred_supplier(item_code, req_date)
            if pref:
                return {
                    "decision": "PO",
                    "route": "SPOT_PO",
                    "supplier_id": pref.supplier_id,
                    "unit_price": pref.reference_price,
                    "group_value_inr": req_value,
                    "suggested_supplier_ids": None,
                    "reason": f"Policy clause 5.4: Spot PO (value < {int(spot_limit)}, bought in last 365d) to 1st preferred supplier {pref.supplier_id}"
                }

        # Check RFQ (Rule 5.5)
        # Value < 10,00,000 (including small items never bought in last 365 days)
        rfq_limit = 1000000.0
        for r in self.policy.rules:
            if r.route == "RFQ":
                rfq_limit = r.condition.get("max_value_exclusive", 1000000.0)

        if req_value < rfq_limit:
            suggested = self.preferred_service.suggest_suppliers_for_sourcing(item_code, 3, req_date)
            reason_detail = "no contract and value between 2L and 10L" if bought_in_last_365_active else "small item not bought in last 365 days"
            return {
                "decision": "SOURCING_REQUEST",
                "route": "RFQ",
                "supplier_id": None,
                "unit_price": None,
                "group_value_inr": req_value,
                "suggested_supplier_ids": ";".join(suggested) if suggested else None,
                "reason": f"Policy clause 5.5: RFQ sourcing ({reason_detail}); suggested top suppliers"
            }

        # Rule 5.6: Value >= 10,00,000 -> RFP
        suggested = self.preferred_service.suggest_suppliers_for_sourcing(item_code, 5, req_date)
        return {
            "decision": "SOURCING_REQUEST",
            "route": "RFP",
            "supplier_id": None,
            "unit_price": None,
            "group_value_inr": req_value,
            "suggested_supplier_ids": ";".join(suggested) if suggested else None,
            "reason": f"Policy clause 5.6: Formal RFP sourcing for high-value requirement (>= 10L); suggested {len(suggested)} suppliers"
        }
