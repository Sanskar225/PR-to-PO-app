from dataclasses import dataclass, field
from datetime import date
from typing import Dict
from app.core.exceptions import ContractCeilingExceededException

@dataclass
class RateContract:
    contract_id: str
    supplier_id: str
    supplier_name: str
    start_date: date
    end_date: date
    value_cap: float
    consumed_value: float = 0.0
    rates: Dict[str, float] = field(default_factory=dict)
    is_pdf_extracted: bool = False

    @property
    def remaining_ceiling(self) -> float:
        return max(0.0, self.value_cap - self.consumed_value)

    def is_valid_on(self, ref_date: date) -> bool:
        """Policy Clause 4.1: Requirement date falls between start and end dates (inclusive)."""
        return self.start_date <= ref_date <= self.end_date

    def covers_item(self, item_code: str) -> bool:
        return item_code in self.rates

    def get_rate(self, item_code: str) -> float:
        return self.rates.get(item_code, 0.0)

    def can_accommodate(self, amount: float) -> bool:
        """Policy Clause 4.2: Consumed value + requirement's value must not exceed contract value ceiling."""
        return (self.consumed_value + amount) <= self.value_cap

    def consume_ceiling(self, amount: float) -> None:
        """Enforces domain invariant on ceiling consumption."""
        if not self.can_accommodate(amount):
            raise ContractCeilingExceededException(
                contract_id=self.contract_id,
                requested_val=amount,
                available_ceiling=self.remaining_ceiling
            )
        self.consumed_value += amount
