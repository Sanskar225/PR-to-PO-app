import json
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.domain.entities.item import Item, ItemType
from app.domain.entities.supplier import Supplier, SupplierStatus
from app.domain.entities.contract import RateContract
from app.domain.entities.requirement import RequirementGroup
from app.domain.entities.pr_line import PurchaseRequisitionLine, UrgencyLevel
from app.domain.policies.policy_document import PolicyDocumentAggregate
from app.domain.repositories.interfaces import (
    IItemRepository, ISupplierRepository, IContractRepository,
    IPOHistoryRepository, IRequirementRepository, IPolicyRepository, IAuditRepository
)
from app.db.models import (
    ItemModel, SupplierModel, ContractModel, ContractLineModel,
    POHistoryModel, PRBatchModel, PRLineModel, RequirementGroupModel,
    DecisionModel, PolicyVersionModel, AuditLogModel
)

class SQLItemRepository(IItemRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, item_code: str) -> Optional[Item]:
        row = self.db.query(ItemModel).filter(ItemModel.item_code == item_code).first()
        if not row:
            return None
        return Item(
            item_code=row.item_code,
            description=row.description,
            uom=row.uom,
            category=row.category,
            item_type=ItemType.from_str(row.item_type),
            standard_price=row.standard_price
        )

    def get_all(self) -> List[Item]:
        rows = self.db.query(ItemModel).all()
        return [
            Item(
                item_code=r.item_code,
                description=r.description,
                uom=r.uom,
                category=r.category,
                item_type=ItemType.from_str(r.item_type),
                standard_price=r.standard_price
            )
            for r in rows
        ]

    def get_all_indexed(self) -> Dict[str, Item]:
        return {item.item_code: item for item in self.get_all()}


class SQLSupplierRepository(ISupplierRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, supplier_id: str) -> Optional[Supplier]:
        row = self.db.query(SupplierModel).filter(SupplierModel.supplier_id == supplier_id).first()
        if not row:
            return None
        cats = [c.strip() for c in (row.categories or "").split(";") if c.strip()]
        return Supplier(
            supplier_id=row.supplier_id,
            name=row.name,
            city=row.city or "",
            categories=cats,
            status=SupplierStatus.from_str(row.status),
            on_time_pct=row.on_time_pct,
            quality_rating=row.quality_rating
        )

    def get_all(self) -> List[Supplier]:
        rows = self.db.query(SupplierModel).all()
        result = []
        for r in rows:
            cats = [c.strip() for c in (r.categories or "").split(";") if c.strip()]
            result.append(Supplier(
                supplier_id=r.supplier_id,
                name=r.name,
                city=r.city or "",
                categories=cats,
                status=SupplierStatus.from_str(r.status),
                on_time_pct=r.on_time_pct,
                quality_rating=r.quality_rating
            ))
        return result

    def get_all_active(self) -> List[Supplier]:
        return [s for s in self.get_all() if s.is_eligible]


class SQLContractRepository(IContractRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[RateContract]:
        rows = self.db.query(ContractModel).all()
        result = []
        for r in rows:
            rate_map = {line.item_code: line.rate for line in r.lines}
            s_d = date.fromisoformat(r.start_date[:10])
            e_d = date.fromisoformat(r.end_date[:10])
            result.append(RateContract(
                contract_id=r.contract_id,
                supplier_id=r.supplier_id,
                supplier_name=r.supplier_name,
                start_date=s_d,
                end_date=e_d,
                value_cap=r.value_cap,
                consumed_value=r.consumed_value,
                rates=rate_map,
                is_pdf_extracted=r.is_pdf_extracted
            ))
        return result

    def get_contracts_covering_item(self, item_code: str) -> List[RateContract]:
        return [c for c in self.get_all() if c.covers_item(item_code)]

    def save(self, contract: RateContract) -> None:
        c_row = self.db.query(ContractModel).filter(ContractModel.contract_id == contract.contract_id).first()
        if not c_row:
            c_row = ContractModel(
                contract_id=contract.contract_id,
                supplier_id=contract.supplier_id,
                supplier_name=contract.supplier_name,
                start_date=contract.start_date.isoformat(),
                end_date=contract.end_date.isoformat(),
                value_cap=contract.value_cap,
                consumed_value=contract.consumed_value,
                is_pdf_extracted=contract.is_pdf_extracted
            )
            self.db.add(c_row)
            self.db.flush()
            for code, rate in contract.rates.items():
                self.db.add(ContractLineModel(
                    contract_id=contract.contract_id,
                    item_code=code,
                    description="",
                    rate=rate
                ))
        else:
            c_row.consumed_value = contract.consumed_value
        self.db.commit()


class SQLPOHistoryRepository(IPOHistoryRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Any]:
        return self.db.query(POHistoryModel).all()

    def get_by_item(self, item_code: str) -> List[Any]:
        return self.db.query(POHistoryModel).filter(POHistoryModel.item_code == item_code).all()


class SQLRequirementRepository(IRequirementRepository):
    def __init__(self, db: Session):
        self.db = db

    def save_batch_results(
        self,
        batch_id: str,
        filename: str,
        requirements: List[RequirementGroup]
    ) -> None:
        total_pr_lines = sum(len(g.lines) for g in requirements)
        batch = PRBatchModel(
            batch_id=batch_id,
            filename=filename,
            total_lines=total_pr_lines,
            policy_version_applied=requirements[0].policy_version if requirements else "5.0"
        )
        self.db.add(batch)

        for g in requirements:
            req_model = RequirementGroupModel(
                group_id=g.group_id,
                batch_id=batch_id,
                plant=g.plant,
                resolved_item_code=g.resolved_item_code,
                total_quantity=g.total_quantity,
                uom=g.first_pr.uom,
                group_value_inr=g.group_value_inr,
                decision=g.decision or "PO",
                route=g.route or "SPOT_PO",
                po_id=g.po_id,
                supplier_id=g.supplier_id,
                unit_price=g.unit_price,
                suggested_supplier_ids=g.suggested_supplier_ids,
                policy_version=g.policy_version,
                reason=g.reason,
                status="APPROVED" if g.po_id else "PENDING"
            )
            self.db.add(req_model)

            for line in g.lines:
                pr_m = PRLineModel(
                    batch_id=batch_id,
                    pr_no=line.pr_no,
                    pr_line=line.pr_line,
                    created_at=line.created_at.strftime("%Y-%m-%d %H:%M"),
                    requester=line.requester,
                    department=line.department,
                    plant=line.plant,
                    item_code=line.item_code,
                    description=line.description,
                    quantity=line.quantity,
                    uom=line.uom,
                    estimated_unit_price=line.estimated_unit_price,
                    need_by_date=line.need_by_date.isoformat(),
                    urgency=line.urgency.value
                )
                self.db.add(pr_m)

                dec_m = DecisionModel(
                    batch_id=batch_id,
                    pr_no=line.pr_no,
                    pr_line=line.pr_line,
                    resolved_item_code=g.resolved_item_code,
                    group_id=g.group_id,
                    po_id=g.po_id,
                    decision=g.decision or "PO",
                    route=g.route or "SPOT_PO",
                    supplier_id=g.supplier_id,
                    unit_price=g.unit_price,
                    group_value_inr=g.group_value_inr,
                    suggested_supplier_ids=g.suggested_supplier_ids,
                    policy_version=g.policy_version,
                    reason=g.reason
                )
                self.db.add(dec_m)

        self.db.commit()

    def get_all_requirements(self) -> List[RequirementGroup]:
        rows = self.db.query(RequirementGroupModel).order_by(RequirementGroupModel.created_at.desc()).all()
        result = []
        for r in rows:
            pr_rows = self.db.query(PRLineModel).filter(PRLineModel.batch_id == r.batch_id).all()
            dummy_first_pr = PurchaseRequisitionLine(
                pr_no=r.group_id,
                pr_line=1,
                created_at=r.created_at,
                requester="Employee",
                department="Operations",
                plant=r.plant,
                item_code=r.resolved_item_code,
                description="",
                quantity=r.total_quantity,
                uom=r.uom,
                estimated_unit_price=r.unit_price,
                need_by_date=r.created_at.date()
            )
            g = RequirementGroup(
                group_id=r.group_id,
                resolved_item_code=r.resolved_item_code,
                plant=r.plant,
                first_pr=dummy_first_pr
            )
            g.decision = r.decision
            g.route = r.route
            g.po_id = r.po_id
            g.supplier_id = r.supplier_id
            g.unit_price = r.unit_price
            g.group_value_inr = r.group_value_inr
            g.suggested_supplier_ids = r.suggested_supplier_ids
            g.policy_version = r.policy_version
            g.reason = r.reason
            g.status = r.status
            result.append(g)
        return result

    def get_by_group_id(self, group_id: str) -> Optional[RequirementGroup]:
        reqs = self.get_all_requirements()
        for r in reqs:
            if r.group_id == group_id:
                return r
        return None

    def update_requirement(self, requirement: RequirementGroup) -> None:
        row = self.db.query(RequirementGroupModel).filter(RequirementGroupModel.group_id == requirement.group_id).first()
        if row:
            row.route = requirement.route
            row.supplier_id = requirement.supplier_id
            row.status = requirement.status
            row.reason = requirement.reason
            self.db.commit()


class SQLPolicyRepository(IPolicyRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_active_policy(self) -> PolicyDocumentAggregate:
        row = self.db.query(PolicyVersionModel).filter(PolicyVersionModel.is_active == True).first()
        if not row:
            # Fallback to 5.0
            row = self.db.query(PolicyVersionModel).filter(PolicyVersionModel.version == "5.0").first()
        if not row:
            # Load default JSON
            from app.core.config import POLICIES_DIR
            with open(POLICIES_DIR / "policy_v5_0.json", "r") as fp:
                data = json.load(fp)
                return PolicyDocumentAggregate.from_dict(data)
        data = json.loads(row.rules_json)
        return PolicyDocumentAggregate.from_dict(data)

    def get_by_version(self, version: str) -> Optional[PolicyDocumentAggregate]:
        row = self.db.query(PolicyVersionModel).filter(PolicyVersionModel.version == version).first()
        if not row:
            return None
        data = json.loads(row.rules_json)
        return PolicyDocumentAggregate.from_dict(data)

    def get_all_versions(self) -> List[str]:
        rows = self.db.query(PolicyVersionModel).all()
        return [r.version for r in rows]

    def save_version(self, policy: PolicyDocumentAggregate) -> None:
        existing = self.db.query(PolicyVersionModel).filter(PolicyVersionModel.version == policy.version).first()
        raw_json = json.dumps(policy.raw_data)
        if not existing:
            existing = PolicyVersionModel(
                version=policy.version,
                policy_id=policy.policy_id,
                name=policy.name,
                effective_date=policy.effective_date,
                owner=policy.owner,
                rules_json=raw_json,
                is_active=False
            )
            self.db.add(existing)
        else:
            existing.rules_json = raw_json
        self.db.commit()

    def set_active_version(self, version: str) -> None:
        self.db.query(PolicyVersionModel).update({PolicyVersionModel.is_active: False})
        target = self.db.query(PolicyVersionModel).filter(PolicyVersionModel.version == version).first()
        if target:
            target.is_active = True
        self.db.commit()


class SQLAuditRepository(IAuditRepository):
    def __init__(self, db: Session):
        self.db = db

    def record_audit(
        self,
        group_id: Optional[str],
        actor: str,
        action: str,
        details: str,
        comment: Optional[str] = None,
        override_route: Optional[str] = None,
        override_supplier_id: Optional[str] = None
    ) -> None:
        log_entry = AuditLogModel(
            group_id=group_id,
            actor=actor,
            action=action,
            details=details,
            comment=comment,
            override_route=override_route,
            override_supplier_id=override_supplier_id,
            timestamp=datetime.utcnow()
        )
        self.db.add(log_entry)
        self.db.commit()

    def get_all_logs(self) -> List[Dict[str, Any]]:
        rows = self.db.query(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else "",
                "group_id": r.group_id,
                "actor": r.actor,
                "action": r.action,
                "details": r.details,
                "comment": r.comment,
                "override_route": r.override_route,
                "override_supplier_id": r.override_supplier_id
            }
            for r in rows
        ]
