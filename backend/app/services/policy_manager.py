import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pypdf

from app.core.config import POLICIES_DIR, DEFAULT_POLICY_VERSION
from app.models.schemas import PolicyDocument, PolicyRule, PolicyDiff

class PolicyManager:
    def __init__(self, policies_dir: Path = POLICIES_DIR):
        self.policies_dir = policies_dir
        self.policies: Dict[str, PolicyDocument] = {}
        self.active_version: str = DEFAULT_POLICY_VERSION
        self.pending_amendments: Dict[str, Tuple[PolicyDocument, PolicyDiff]] = {}
        
        self.load_all_policies()

    def load_all_policies(self):
        for f in self.policies_dir.glob("policy_v*.json"):
            try:
                with open(f, "r") as fp:
                    data = json.load(fp)
                    doc = PolicyDocument(**data)
                    self.policies[doc.version] = doc
            except Exception as e:
                print(f"Error loading policy from {f}: {e}")

        # Ensure v5.0 exists
        if "5.0" in self.policies:
            self.active_version = "5.0"
        elif self.policies:
            self.active_version = list(self.policies.keys())[0]

    def get_active_policy(self) -> PolicyDocument:
        if self.active_version in self.policies:
            return self.policies[self.active_version]
        # fallback
        return list(self.policies.values())[0]

    def set_active_version(self, version: str):
        if version in self.policies:
            self.active_version = version
            try:
                from app.db.session import SessionLocal
                from app.db.models import PolicyVersionModel
                db = SessionLocal()
                try:
                    for row in db.query(PolicyVersionModel).all():
                        row.is_active = (row.version == version)
                    db.commit()
                finally:
                    db.close()
            except Exception:
                pass

    def parse_amendment_text(self, text: str, base_version: Optional[str] = None) -> PolicyDiff:
        """
        Parses amendment text or document contents, produces candidate PolicyDocument and PolicyDiff.
        """
        base = self.policies.get(base_version or self.active_version) or self.get_active_policy()
        new_doc_data = base.model_dump()
        
        # Determine next version
        v_num_match = re.search(r"version\s*[:=]?\s*([0-9]+\.[0-9]+)", text, re.IGNORECASE)
        if v_num_match:
            new_version = v_num_match.group(1).strip()
        else:
            try:
                major, minor = base.version.split(".")
                new_version = f"{major}.{int(minor)+1}"
            except Exception:
                new_version = f"{base.version}.1"

        new_doc_data["version"] = new_version

        # Effective date
        date_match = re.search(r"effective\s*(?:from|date)?\s*[:=]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.IGNORECASE)
        if date_match:
            new_doc_data["effective_date"] = date_match.group(1).strip()
        else:
            new_doc_data["effective_date"] = datetime.now().strftime("%Y-%m-%d")

        summary_changes: List[str] = []
        rule_changes: List[Dict[str, Any]] = []

        # 1. Spot PO threshold change
        # e.g. 'Spot PO limit is increased to INR 300,000' or 'Spot PO limit to 300000'
        spot_match = re.search(r"spot\s*(?:po)?\s*[^0-9\n\r]*?([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{5,8})", text, re.IGNORECASE)
        if spot_match:
            val_str = spot_match.group(1).replace(",", "").strip()
            try:
                new_spot_limit = float(val_str)
                for r in new_doc_data["rules"]:
                    if r["route"] == "SPOT_PO":
                        old_val = r["condition"].get("max_value_exclusive", 200000)
                        r["condition"]["max_value_exclusive"] = new_spot_limit
                        summary_changes.append(f"Spot PO threshold changed from ₹{old_val:,.0f} to ₹{new_spot_limit:,.0f}")
                        rule_changes.append({"rule_id": r["rule_id"], "field": "max_value_exclusive", "old": old_val, "new": new_spot_limit})
            except ValueError:
                pass

        # 2. Emergency PO threshold change
        # e.g. 'Emergency PO threshold is increased to INR 750,000'
        emerg_match = re.search(r"emergency\s*(?:po)?\s*[^0-9\n\r]*?([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{5,8})", text, re.IGNORECASE)
        if emerg_match:
            val_str = emerg_match.group(1).replace(",", "").strip()
            try:
                new_emerg_limit = float(val_str)
                for r in new_doc_data["rules"]:
                    if r["route"] == "EMERGENCY_PO":
                        old_val = r["condition"].get("max_value", 500000)
                        r["condition"]["max_value"] = new_emerg_limit
                        summary_changes.append(f"Emergency PO threshold changed from ₹{old_val:,.0f} to ₹{new_emerg_limit:,.0f}")
                        rule_changes.append({"rule_id": r["rule_id"], "field": "max_value", "old": old_val, "new": new_emerg_limit})
            except ValueError:
                pass

        # 3. RFQ threshold change
        rfq_match = re.search(r"rfq\s*[^0-9\n\r]*?([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{5,8})", text, re.IGNORECASE)
        if rfq_match:
            val_str = rfq_match.group(1).replace(",", "").strip()
            try:
                new_rfq_limit = float(val_str)
                for r in new_doc_data["rules"]:
                    if r["route"] == "RFQ":
                        old_val = r["condition"].get("max_value_exclusive", 1000000)
                        r["condition"]["max_value_exclusive"] = new_rfq_limit
                        summary_changes.append(f"RFQ ceiling threshold changed from ₹{old_val:,.0f} to ₹{new_rfq_limit:,.0f}")
                        rule_changes.append({"rule_id": r["rule_id"], "field": "max_value_exclusive", "old": old_val, "new": new_rfq_limit})
            except ValueError:
                pass

        # 4. Plant specific rule addition
        # e.g. "For plant CHK1, direct POs above 100000 require approval" or "Add rule for PUN1: ..."
        plant_match = re.search(r"plant\s*([A-Z0-9]+)\s*[:,\-]?\s*(.+)", text, re.IGNORECASE)
        if plant_match:
            p_code = plant_match.group(1).strip().upper()
            detail = plant_match.group(2).strip()
            # Add as new plant rule
            new_rule_id = f"5.{len(new_doc_data['rules']) + 1}"
            new_rule = {
                "rule_id": new_rule_id,
                "name": f"Plant {p_code} Special Rule",
                "clause": new_rule_id,
                "condition": {"plant": [p_code]},
                "outcome": "PO",
                "route": "SPOT_PO",
                "notes": detail
            }
            new_doc_data["rules"].insert(3, new_rule)
            summary_changes.append(f"Added special procurement rule for Plant {p_code}: {detail}")
            rule_changes.append({"action": "added_rule", "rule": new_rule})

        # 5. Clubbing window changes
        # e.g. "Clubbing window to 21 days"
        club_match = re.search(r"clubbing\s*(?:window)?\s*(?:to|is)?\s*([0-9]+)\s*days", text, re.IGNORECASE)
        if club_match:
            new_days = int(club_match.group(1).strip())
            old_days = new_doc_data["clubbing_rules"].get("creation_window_days", 14)
            new_doc_data["clubbing_rules"]["creation_window_days"] = new_days
            summary_changes.append(f"Clubbing window changed from {old_days} days to {new_days} days")
            rule_changes.append({"field": "creation_window_days", "old": old_days, "new": new_days})

        if not summary_changes:
            summary_changes.append("General policy text updated with revised guidelines.")

        diff_md = f"### Policy Amendment Preview: Version {base.version} → {new_version}\n"
        diff_md += f"**Effective Date:** {new_doc_data['effective_date']}\n\n"
        diff_md += "**Key Changes:**\n"
        for s in summary_changes:
            diff_md += f"- {s}\n"

        new_policy_doc = PolicyDocument(**new_doc_data)
        policy_diff = PolicyDiff(
            base_version=base.version,
            new_version=new_version,
            effective_date=new_doc_data["effective_date"],
            summary_of_changes=summary_changes,
            rule_changes=rule_changes,
            diff_markdown=diff_md
        )

        self.pending_amendments[new_version] = (new_policy_doc, policy_diff)
        return policy_diff

    def parse_amendment_pdf(self, pdf_path: Path, base_version: Optional[str] = None) -> PolicyDiff:
        reader = pypdf.PdfReader(str(pdf_path))
        full_text = ""
        for p in reader.pages:
            t = p.extract_text()
            if t:
                full_text += "\n" + t
        return self.parse_amendment_text(full_text, base_version)

    def approve_amendment(self, new_version: str) -> Optional[PolicyDocument]:
        """
        Approves and activates a pending amendment. Saves as policy_v{clean_ver}.json
        """
        if new_version not in self.pending_amendments:
            return None

        doc, diff = self.pending_amendments.pop(new_version)
        clean_name = f"policy_v{doc.version.replace('.', '_')}.json"
        save_path = self.policies_dir / clean_name

        with open(save_path, "w") as fp:
            json.dump(doc.model_dump(), fp, indent=2)

        self.policies[doc.version] = doc
        self.active_version = doc.version
        try:
            from app.db.session import SessionLocal
            from app.db.models import PolicyVersionModel
            db = SessionLocal()
            try:
                for row in db.query(PolicyVersionModel).all():
                    row.is_active = False
                existing = db.query(PolicyVersionModel).filter_by(version=doc.version).first()
                if existing:
                    existing.is_active = True
                    existing.rules_json = json.dumps(doc.model_dump())
                else:
                    db.add(PolicyVersionModel(
                        version=doc.version,
                        policy_id=doc.policy_id,
                        name=doc.name,
                        effective_date=doc.effective_date,
                        owner=doc.owner,
                        rules_json=json.dumps(doc.model_dump()),
                        is_active=True
                    ))
                db.commit()
            finally:
                db.close()
        except Exception:
            pass
        return doc

policy_manager = PolicyManager()
