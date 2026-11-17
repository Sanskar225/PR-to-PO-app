from datetime import date, timedelta
from typing import List, Tuple, Optional, Any
from app.domain.entities.requirement import RequirementGroup
from app.domain.entities.contract import RateContract

class ValuationResult:
    def __init__(
        self,
        unit_price: float,
        total_value: float,
        source: str,
        selected_contract: Optional[RateContract] = None,
        selected_contract_rate: Optional[float] = None,
        lowest_applicable_contract_rate: Optional[float] = None
    ):
        self.unit_price = unit_price
        self.total_value = total_value
        self.source = source
        self.selected_contract = selected_contract
        self.selected_contract_rate = selected_contract_rate
        self.lowest_applicable_contract_rate = lowest_applicable_contract_rate

class ValuationDomainService:
    @staticmethod
    def value_requirement(
        requirement: RequirementGroup,
        available_contracts: List[RateContract],
        recent_pos_365d: List[Any],
        standard_price: float
    ) -> ValuationResult:
        """
        Executes Policy Clause 3.1:
        Requirement value = total quantity x unit price, where unit price is the first of:
        (a) Rate of contract that will be used (4.3), or, if every applicable contract is out
            of ceiling, the lowest applicable contract rate;
        (b) Price on the most recent PO for the item in the 365 days before requirement date;
        (c) Item master standard price.
        For NEW items: requester estimated unit price.
        """
        total_qty = requirement.total_quantity
        req_date = requirement.requirement_date

        # Case 1: NEW item
        if requirement.resolved_item_code == "NEW":
            est_price = requirement.first_pr.estimated_unit_price or 0.0
            return ValuationResult(
                unit_price=est_price,
                total_value=total_qty * est_price,
                source="requester estimate"
            )

        # Case 2: Filter applicable contracts (Clause 4.1)
        # Covers item, req_date between start and end (inclusive)
        applicable: List[Tuple[RateContract, float]] = []
        for c in available_contracts:
            if c.covers_item(requirement.resolved_item_code) and c.is_valid_on(req_date):
                applicable.append((c, c.get_rate(requirement.resolved_item_code)))

        # Sort by rate ascending (lowest rate first - Clause 4.3)
        applicable.sort(key=lambda x: x[1])

        lowest_rate = applicable[0][1] if applicable else None
        selected_contract: Optional[RateContract] = None
        selected_contract_rate: Optional[float] = None

        # Check ceiling room
        for c, rate in applicable:
            val_at_rate = total_qty * rate
            if c.can_accommodate(val_at_rate):
                selected_contract = c
                selected_contract_rate = rate
                break

        if selected_contract_rate is not None:
            val = total_qty * selected_contract_rate
            return ValuationResult(
                unit_price=selected_contract_rate,
                total_value=val,
                source=f"contract {selected_contract.contract_id}",
                selected_contract=selected_contract,
                selected_contract_rate=selected_contract_rate,
                lowest_applicable_contract_rate=lowest_rate
            )

        if lowest_rate is not None:
            val = total_qty * lowest_rate
            return ValuationResult(
                unit_price=lowest_rate,
                total_value=val,
                source="lowest contract rate (ceiling exhausted)",
                lowest_applicable_contract_rate=lowest_rate
            )

        # Check most recent PO in past 365 days
        if recent_pos_365d:
            # Sort by date descending, then po_number descending
            sorted_pos = sorted(
                recent_pos_365d,
                key=lambda p: (p.po_date, str(p.po_number)),
                reverse=True
            )
            po_price = sorted_pos[0].unit_price
            return ValuationResult(
                unit_price=po_price,
                total_value=total_qty * po_price,
                source=f"recent PO {sorted_pos[0].po_number}"
            )

        # Fallback to standard price
        return ValuationResult(
            unit_price=standard_price,
            total_value=total_qty * standard_price,
            source="item master standard price"
        )
