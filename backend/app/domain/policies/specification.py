from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.domain.entities.requirement import RequirementGroup

class EvaluationContext:
    """Context holding auxiliary lookup data needed for specification evaluation."""
    def __init__(
        self,
        item_master_item: Optional[Any],
        has_valid_contract: bool,
        selected_contract: Optional[Any],
        selected_contract_rate: Optional[float],
        bought_in_last_365_days: bool,
        requirement_value: float,
        first_preferred_supplier: Optional[Any] = None
    ):
        self.item_master_item = item_master_item
        self.has_valid_contract = has_valid_contract
        self.selected_contract = selected_contract
        self.selected_contract_rate = selected_contract_rate
        self.bought_in_last_365_days = bought_in_last_365_days
        self.requirement_value = requirement_value
        self.first_preferred_supplier = first_preferred_supplier

class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        pass

    def __and__(self, other: "Specification") -> "Specification":
        return AndSpecification(self, other)

    def __or__(self, other: "Specification") -> "Specification":
        return OrSpecification(self, other)

    def __invert__(self) -> "Specification":
        return NotSpecification(self)

class AndSpecification(Specification):
    def __init__(self, spec_a: Specification, spec_b: Specification):
        self.spec_a = spec_a
        self.spec_b = spec_b

    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        return self.spec_a.is_satisfied_by(requirement, context) and self.spec_b.is_satisfied_by(requirement, context)

class OrSpecification(Specification):
    def __init__(self, spec_a: Specification, spec_b: Specification):
        self.spec_a = spec_a
        self.spec_b = spec_b

    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        return self.spec_a.is_satisfied_by(requirement, context) or self.spec_b.is_satisfied_by(requirement, context)

class NotSpecification(Specification):
    def __init__(self, spec: Specification):
        self.spec = spec

    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        return not self.spec.is_satisfied_by(requirement, context)

# Concrete Policy Specifications

class CapexSpecification(Specification):
    """Policy 5.1: Item type is Capex."""
    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        if context.item_master_item and hasattr(context.item_master_item, "is_capex"):
            return context.item_master_item.is_capex
        return False

class ValidContractSpecification(Specification):
    """Policy 5.2: A rate contract can be used (active, covering item, within dates, ceiling remaining)."""
    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        return context.has_valid_contract and (context.selected_contract is not None)

class EmergencyPOSpecification(Specification):
    """Policy 5.3: Emergency, value <= max_val (default 5L), bought in last 365 days."""
    def __init__(self, max_value: float = 500000.0):
        self.max_value = max_value

    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        return (
            requirement.is_emergency and
            context.requirement_value <= self.max_value and
            context.bought_in_last_365_days and
            (context.first_preferred_supplier is not None)
        )

class SpotPOSpecification(Specification):
    """Policy 5.4: Value below limit (default 2L), bought from an Active supplier in last 365 days."""
    def __init__(self, max_value_exclusive: float = 200000.0):
        self.max_value_exclusive = max_value_exclusive

    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        return (
            context.requirement_value < self.max_value_exclusive and
            context.bought_in_last_365_days and
            (context.first_preferred_supplier is not None)
        )

class RFQSpecification(Specification):
    """Policy 5.5: Value below ceiling (default 10L)."""
    def __init__(self, max_value_exclusive: float = 1000000.0):
        self.max_value_exclusive = max_value_exclusive

    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        return context.requirement_value < self.max_value_exclusive

class RFPSpecification(Specification):
    """Policy 5.6: Value at or above threshold (default 10L)."""
    def __init__(self, min_value: float = 1000000.0):
        self.min_value = min_value

    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        return context.requirement_value >= self.min_value

class PlantSpecification(Specification):
    """Plant-specific constraint (e.g. only applies to CHK1 or PUN1)."""
    def __init__(self, plant: str):
        self.plant = plant.upper()

    def is_satisfied_by(self, requirement: RequirementGroup, context: EvaluationContext) -> bool:
        return requirement.plant.upper() == self.plant
