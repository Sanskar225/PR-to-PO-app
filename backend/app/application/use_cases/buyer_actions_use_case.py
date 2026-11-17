from typing import Dict, Any, List
from app.domain.repositories.interfaces import IRequirementRepository, IAuditRepository
from app.core.exceptions import DomainException

class BuyerActionsUseCase:
    def __init__(self, requirement_repo: IRequirementRepository, audit_repo: IAuditRepository):
        self.requirement_repo = requirement_repo
        self.audit_repo = audit_repo

    def get_workspace_overview(self) -> Dict[str, Any]:
        reqs = self.requirement_repo.get_all_requirements()
        logs = self.audit_repo.get_all_logs()

        # Index logs by group_id
        logs_by_group: Dict[str, List[Any]] = {}
        for l in logs:
            gid = l.get("group_id")
            if gid:
                if gid not in logs_by_group:
                    logs_by_group[gid] = []
                logs_by_group[gid].append(l)

        req_list = []
        for r in reqs:
            req_list.append({
                "group_id": r.group_id,
                "resolved_item_code": r.resolved_item_code,
                "plant": r.plant,
                "decision": r.decision,
                "route": r.route,
                "po_id": r.po_id,
                "supplier_id": r.supplier_id,
                "unit_price": r.unit_price,
                "group_value_inr": r.group_value_inr,
                "suggested_supplier_ids": r.suggested_supplier_ids,
                "policy_version": r.policy_version,
                "reason": r.reason,
                "status": r.status,
                "pr_lines": [{"pr_no": l.pr_no, "pr_line": l.pr_line} for l in r.lines],
                "audit_trail": logs_by_group.get(r.group_id, [])
            })

        summary = {
            "total_requirements": len(req_list),
            "total_pos": sum(1 for r in req_list if r["decision"] == "PO"),
            "total_sourcing": sum(1 for r in req_list if r["decision"] == "SOURCING_REQUEST"),
            "total_value": sum(r["group_value_inr"] for r in req_list)
        }

        return {
            "summary": summary,
            "requirements": req_list
        }

    def approve_requirement(self, group_id: str, buyer_name: str = "Procurement Buyer") -> None:
        req = self.requirement_repo.get_by_group_id(group_id)
        if not req:
            raise DomainException(f"Requirement {group_id} not found.")

        req.status = "APPROVED"
        self.requirement_repo.update_requirement(req)

        self.audit_repo.record_audit(
            group_id=group_id,
            actor=buyer_name,
            action="APPROVE",
            details=f"Requirement {group_id} approved by buyer",
            comment="Approved for procurement execution"
        )

    def override_requirement(
        self,
        group_id: str,
        override_route: str,
        override_supplier_id: str,
        comment: str,
        buyer_name: str = "Procurement Buyer"
    ) -> None:
        if not comment or not comment.strip():
            raise DomainException("Override requires a mandatory written justification (Policy 8.1).")

        req = self.requirement_repo.get_by_group_id(group_id)
        if not req:
            raise DomainException(f"Requirement {group_id} not found.")

        req.status = "OVERRIDDEN"
        if override_route:
            req.route = override_route
        if override_supplier_id:
            req.supplier_id = override_supplier_id
        req.reason += f" | Buyer Override: {comment} (by {buyer_name})"

        self.requirement_repo.update_requirement(req)

        self.audit_repo.record_audit(
            group_id=group_id,
            actor=buyer_name,
            action="OVERRIDE",
            details=f"Decision overridden to route {override_route}",
            comment=comment,
            override_route=override_route,
            override_supplier_id=override_supplier_id
        )
