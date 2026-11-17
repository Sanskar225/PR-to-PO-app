import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from app.domain.repositories.interfaces import IPolicyRepository, IAuditRepository
from app.domain.policies.policy_document import PolicyDocumentAggregate
from app.application.dto.schemas import PolicyDiffDTO

class ApplyPolicyAmendmentUseCase:
    def __init__(self, policy_repo: IPolicyRepository, audit_repo: IAuditRepository):
        self.policy_repo = policy_repo
        self.audit_repo = audit_repo
        # Memory buffer for unapproved diffs awaiting approval
        self.pending_diffs: Dict[str, Tuple[Dict[str, Any], PolicyDiffDTO]] = {}

    def parse_amendment(self, text: str, base_version: Optional[str] = None) -> PolicyDiffDTO:
        base_policy = (
            self.policy_repo.get_by_version(base_version)
            if base_version
            else self.policy_repo.get_active_policy()
        )
        new_data = dict(base_policy.raw_data)

        # 1. Version derivation
        v_match = re.search(r"version\s*[:=]?\s*([0-9]+\.[0-9]+)", text, re.IGNORECASE)
        if v_match:
            new_version = v_match.group(1).strip()
        else:
            try:
                major, minor = base_policy.version.split(".")
                new_version = f"{major}.{int(minor) + 1}"
            except Exception:
                new_version = f"{base_policy.version}.1"

        new_data["version"] = new_version

        # 2. Effective date
        d_match = re.search(r"effective\s*(?:from|date)?\s*[:=]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.IGNORECASE)
        new_data["effective_date"] = d_match.group(1).strip() if d_match else datetime.now().strftime("%Y-%m-%d")

        summary_changes: List[str] = []
        rule_changes: List[Dict[str, Any]] = []

        # 3. Spot PO limit revision
        spot_match = re.search(r"spot\s*(?:po)?\s*[^0-9\n\r]*?([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{5,8})", text, re.IGNORECASE)
        if spot_match:
            new_limit = float(spot_match.group(1).replace(",", "").strip())
            for r in new_data.get("rules", []):
                if r.get("route") == "SPOT_PO":
                    old_limit = r["condition"].get("max_value_exclusive", 200000.0)
                    r["condition"]["max_value_exclusive"] = new_limit
                    summary_changes.append(f"Spot PO threshold revised from ₹{old_limit:,.0f} to ₹{new_limit:,.0f}")
                    rule_changes.append({"rule": "5.4", "parameter": "max_value_exclusive", "old": old_limit, "new": new_limit})

        # 4. Emergency PO limit revision
        emerg_match = re.search(r"emergency\s*(?:po)?\s*[^0-9\n\r]*?([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{5,8})", text, re.IGNORECASE)
        if emerg_match:
            new_emerg = float(emerg_match.group(1).replace(",", "").strip())
            for r in new_data.get("rules", []):
                if r.get("route") == "EMERGENCY_PO":
                    old_emerg = r["condition"].get("max_value", 500000.0)
                    r["condition"]["max_value"] = new_emerg
                    summary_changes.append(f"Emergency PO threshold revised from ₹{old_emerg:,.0f} to ₹{new_emerg:,.0f}")
                    rule_changes.append({"rule": "5.3", "parameter": "max_value", "old": old_emerg, "new": new_emerg})

        # 5. RFQ ceiling revision
        rfq_match = re.search(r"rfq\s*[^0-9\n\r]*?([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{5,8})", text, re.IGNORECASE)
        if rfq_match:
            new_rfq = float(rfq_match.group(1).replace(",", "").strip())
            for r in new_data.get("rules", []):
                if r.get("route") == "RFQ":
                    old_rfq = r["condition"].get("max_value_exclusive", 1000000.0)
                    r["condition"]["max_value_exclusive"] = new_rfq
                    summary_changes.append(f"RFQ threshold revised from ₹{old_rfq:,.0f} to ₹{new_rfq:,.0f}")
                    rule_changes.append({"rule": "5.5", "parameter": "max_value_exclusive", "old": old_rfq, "new": new_rfq})

        # 6. Plant specific rule addition
        plant_match = re.search(r"plant\s*([A-Z0-9]+)\s*[:,\-]?\s*(.+)", text, re.IGNORECASE)
        if plant_match:
            p_code = plant_match.group(1).strip().upper()
            detail = plant_match.group(2).strip()
            new_rule = {
                "rule_id": f"5.{len(new_data.get('rules', [])) + 1}",
                "name": f"Plant {p_code} Special Rule",
                "clause": f"5.{len(new_data.get('rules', [])) + 1}",
                "condition": {"plant": [p_code]},
                "outcome": "PO",
                "route": "SPOT_PO",
                "notes": detail
            }
            new_data.get("rules", []).insert(3, new_rule)
            summary_changes.append(f"Added Plant-Specific Policy for {p_code}: {detail}")
            rule_changes.append({"action": "rule_added", "rule": new_rule})

        if not summary_changes:
            summary_changes.append("Policy guidelines updated with revised parameters.")

        diff_md = f"### Policy Specification Diff: Version {base_policy.version} → {new_version}\n"
        diff_md += f"**Effective Date:** {new_data['effective_date']}\n\n"
        diff_md += "**Rule AST Modifications:**\n"
        for s in summary_changes:
            diff_md += f"- {s}\n"

        diff_dto = PolicyDiffDTO(
            base_version=base_policy.version,
            new_version=new_version,
            effective_date=new_data["effective_date"],
            summary_of_changes=summary_changes,
            rule_changes=rule_changes,
            diff_markdown=diff_md
        )

        self.pending_diffs[new_version] = (new_data, diff_dto)
        return diff_dto

    def approve_amendment(self, version: str, actor: str = "Procurement Head") -> PolicyDocumentAggregate:
        if version not in self.pending_diffs:
            raise ValueError(f"No pending amendment found for version '{version}'.")

        data, diff = self.pending_diffs.pop(version)
        aggregate = PolicyDocumentAggregate.from_dict(data)

        # Persist through repository
        self.policy_repo.save_version(aggregate)
        self.policy_repo.set_active_version(aggregate.version)

        # Audit log
        self.audit_repo.record_audit(
            group_id=None,
            actor=actor,
            action="POLICY_AMENDMENT_ACTIVATED",
            details=f"Policy version {aggregate.version} activated",
            comment="; ".join(diff.summary_of_changes)
        )

        return aggregate
