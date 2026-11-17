import json
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session

from app.db.session import engine, Base, SessionLocal
from app.db.models import (
    ItemModel, SupplierModel, PlantModel, ContractModel, ContractLineModel,
    POHistoryModel, PolicyVersionModel
)
from app.core.config import MASTER_DATA_DIR, CONTRACTS_DIR, PDF_CONTRACTS_DIR, POLICIES_DIR
from app.services.pdf_contract_extractor import extract_contract_from_pdf

def init_db():
    Base.metadata.create_all(bind=engine)

def seed_database():
    init_db()
    db: Session = SessionLocal()
    try:
        # 1. Plants
        if db.query(PlantModel).count() == 0:
            plants_file = MASTER_DATA_DIR / "plants.csv"
            if plants_file.exists():
                df = pd.read_csv(plants_file)
                for _, row in df.iterrows():
                    p_code = str(row["plant"]).strip()
                    p_name = str(row.get("name", p_code)).strip()
                    db.add(PlantModel(plant=p_code, name=p_name))
                db.commit()
                print(f"Seeded {len(df)} plants.")

        # 2. Items
        if db.query(ItemModel).count() == 0:
            items_file = MASTER_DATA_DIR / "item_master.csv"
            if items_file.exists():
                df = pd.read_csv(items_file)
                for _, row in df.iterrows():
                    db.add(ItemModel(
                        item_code=str(row["item_code"]).strip(),
                        description=str(row["description"]).strip(),
                        uom=str(row["uom"]).strip(),
                        category=str(row["category"]).strip(),
                        item_type=str(row["item_type"]).strip(),
                        standard_price=float(row["standard_price"])
                    ))
                db.commit()
                print(f"Seeded {len(df)} items.")

        # 3. Suppliers
        if db.query(SupplierModel).count() == 0:
            supp_file = MASTER_DATA_DIR / "supplier_master.csv"
            if supp_file.exists():
                df = pd.read_csv(supp_file)
                for _, row in df.iterrows():
                    cat_str = str(row.get("categories", "")) if pd.notna(row.get("categories")) else ""
                    db.add(SupplierModel(
                        supplier_id=str(row["supplier_id"]).strip(),
                        name=str(row["name"]).strip(),
                        city=str(row.get("city", "")).strip(),
                        categories=cat_str,
                        status=str(row["status"]).strip(),
                        on_time_pct=float(row.get("on_time_pct", 0.0)),
                        quality_rating=float(row.get("quality_rating", 0.0))
                    ))
                db.commit()
                print(f"Seeded {len(df)} suppliers.")

        # 4. Contracts & Contract Lines
        if db.query(ContractModel).count() == 0:
            reg_file = CONTRACTS_DIR / "contract_register.csv"
            lines_file = CONTRACTS_DIR / "contract_lines.csv"
            
            contracts_map = {}
            if reg_file.exists():
                df_reg = pd.read_csv(reg_file)
                for _, row in df_reg.iterrows():
                    c_id = str(row["contract_id"]).strip()
                    c_model = ContractModel(
                        contract_id=c_id,
                        supplier_id=str(row["supplier_id"]).strip(),
                        supplier_name=str(row["supplier_name"]).strip(),
                        start_date=str(row["start_date"]).strip(),
                        end_date=str(row["end_date"]).strip(),
                        value_cap=float(row["value_cap"]),
                        consumed_value=float(row.get("consumed_value", 0.0)),
                        is_pdf_extracted=False
                    )
                    db.add(c_model)
                    contracts_map[c_id] = c_model
                db.commit()

            if lines_file.exists():
                df_lines = pd.read_csv(lines_file)
                for _, row in df_lines.iterrows():
                    c_id = str(row["contract_id"]).strip()
                    if c_id in contracts_map:
                        db.add(ContractLineModel(
                            contract_id=c_id,
                            item_code=str(row["item_code"]).strip(),
                            description=str(row.get("description", "")).strip(),
                            uom=str(row.get("uom", "NOS")).strip(),
                            rate=float(row["rate"])
                        ))
                db.commit()

            # PDF contracts (e.g. RC-2026-031, RC-2026-033)
            if PDF_CONTRACTS_DIR.exists():
                for pdf_file in PDF_CONTRACTS_DIR.glob("*.pdf"):
                    extracted = extract_contract_from_pdf(pdf_file)
                    if extracted and extracted.contract_id not in contracts_map:
                        c_model = ContractModel(
                            contract_id=extracted.contract_id,
                            supplier_id=extracted.supplier_id,
                            supplier_name=extracted.supplier_name,
                            start_date=extracted.start_date,
                            end_date=extracted.end_date,
                            value_cap=extracted.value_cap,
                            consumed_value=0.0,
                            is_pdf_extracted=True
                        )
                        db.add(c_model)
                        db.flush()
                        contracts_map[extracted.contract_id] = c_model
                        for itm_code, itm_rate in extracted.lines.items():
                            db.add(ContractLineModel(
                                contract_id=extracted.contract_id,
                                item_code=itm_code,
                                description="",
                                uom="NOS",
                                rate=itm_rate
                            ))
                        db.commit()
                print(f"Seeded {len(contracts_map)} contracts (including PDF extracts).")

        # 5. PO History
        if db.query(POHistoryModel).count() == 0:
            po_file = MASTER_DATA_DIR / "po_history.csv"
            if po_file.exists():
                df = pd.read_csv(po_file)
                for _, row in df.iterrows():
                    delivered_val = row.get("delivered_on_time", True)
                    if isinstance(delivered_val, str):
                        delivered = delivered_val.strip().lower() in ["true", "1", "yes"]
                    else:
                        delivered = bool(delivered_val)
                    db.add(POHistoryModel(
                        po_number=str(row["po_number"]).strip(),
                        po_date=str(row["po_date"]).strip(),
                        supplier_id=str(row["supplier_id"]).strip(),
                        item_code=str(row["item_code"]).strip(),
                        quantity=float(row["quantity"]),
                        uom=str(row.get("uom", "NOS")).strip(),
                        unit_price=float(row["unit_price"]),
                        plant=str(row.get("plant", "")).strip(),
                        delivered_on_time=delivered
                    ))
                db.commit()
                print(f"Seeded {len(df)} historical PO entries.")

        # 6. Policy Versions
        if db.query(PolicyVersionModel).filter_by(version="5.0").count() == 0:
            policy_file = POLICIES_DIR / "policy_v5_0.json"
            if policy_file.exists():
                with open(policy_file, "r") as fp:
                    p_data = json.load(fp)
                    db.add(PolicyVersionModel(
                        version=p_data["version"],
                        policy_id=p_data["policy_id"],
                        name=p_data["name"],
                        effective_date=p_data["effective_date"],
                        owner=p_data["owner"],
                        rules_json=json.dumps(p_data),
                        is_active=True
                    ))
                db.commit()
                print("Seeded Policy Version 5.0 into database.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
