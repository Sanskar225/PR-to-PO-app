from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.domain.policies.rule import DomainPolicyRule
from app.domain.policies.specification import (
    Specification, CapexSpecification, ValidContractSpecification,
    EmergencyPOSpecification, SpotPOSpecification, RFQSpecification,
    RFPSpecification, PlantSpecification
)

@dataclass
class PolicyDocumentAggregate:
    policy_id: str
    version: str
    effective_date: str
    name: str
    owner: str
    applies_to_plants: List[str] = field(default_factory=lambda: ["PUN1", "CHK1"])
    clubbing_creation_window_days: int = 14
    clubbing_need_by_window_days: int = 7
    po_history_lookback_days: int = 365
    preferred_supplier_lookback_days: int = 548
    ranking_weights: Dict[str, float] = field(default_factory=lambda: {
        "po_count": 1.0, "recency": 6.0, "contract": 3.0, "on_time": 2.0, "quality": 2.0
    })
    consolidation_window_hours: int = 24
    rules: List[DomainPolicyRule] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyDocumentAggregate":
        """
        Dynamically compiles declarative JSON policy data into formal Specification ASTs.
        """
        rules: List[DomainPolicyRule] = []
        for r in data.get("rules", []):
            route = r.get("route", "")
            cond = r.get("condition", {})
            spec: Specification

            if route == "CAPEX_SOURCING":
                spec = CapexSpecification()
            elif route == "CONTRACT_PO":
                spec = ValidContractSpecification()
            elif route == "EMERGENCY_PO":
                max_v = cond.get("max_value", 500000.0)
                spec = EmergencyPOSpecification(max_value=max_v)
            elif route == "SPOT_PO":
                limit = cond.get("max_value_exclusive", 200000.0)
                spec = SpotPOSpecification(max_value_exclusive=limit)
            elif route == "RFQ":
                limit = cond.get("max_value_exclusive", 1000000.0)
                spec = RFQSpecification(max_value_exclusive=limit)
            elif route == "RFP":
                min_v = cond.get("min_value", 1000000.0)
                spec = RFPSpecification(min_value=min_v)
            else:
                spec = ValidContractSpecification()

            # Check if plant-specific restriction exists
            if "plant" in cond and cond["plant"]:
                plant_spec = PlantSpecification(cond["plant"][0])
                spec = plant_spec & spec

            rules.append(DomainPolicyRule(
                rule_id=r.get("rule_id", ""),
                name=r.get("name", ""),
                clause=r.get("clause", ""),
                specification=spec,
                outcome=r.get("outcome", ""),
                route=route,
                suggest_count=r.get("suggest_count"),
                supplier_selection=r.get("supplier_selection"),
                requires_approval=r.get("requires_approval")
            ))

        club_cfg = data.get("clubbing_rules", {})
        hist_cfg = data.get("history_lookbacks", {})
        weights_cfg = data.get("ranking_weights", {
            "po_count": 1.0, "recency": 6.0, "contract": 3.0, "on_time": 2.0, "quality": 2.0
        })

        return cls(
            policy_id=data.get("policy_id", "CORVO-PROC-POL-04"),
            version=str(data.get("version", "5.0")),
            effective_date=str(data.get("effective_date", "2026-04-01")),
            name=data.get("name", "Corvo Procurement Policy (PR to PO)"),
            owner=data.get("owner", "Head of Procurement"),
            applies_to_plants=data.get("applies_to_plants", ["PUN1", "CHK1"]),
            clubbing_creation_window_days=club_cfg.get("creation_window_days", 14),
            clubbing_need_by_window_days=club_cfg.get("need_by_window_days", 7),
            po_history_lookback_days=hist_cfg.get("po_history_lookback_days", 365),
            preferred_supplier_lookback_days=hist_cfg.get("preferred_supplier_lookback_days", 548),
            ranking_weights=weights_cfg,
            consolidation_window_hours=data.get("consolidation_window_hours", 24),
            rules=rules,
            raw_data=data
        )
