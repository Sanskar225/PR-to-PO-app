import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from app.core.config import MASTER_DATA_DIR, CONTRACTS_DIR, PDF_CONTRACTS_DIR
from app.models.schemas import Item, Supplier, Plant, Contract, POHistoryEntry
from app.services.pdf_contract_extractor import extract_contract_from_pdf

class DataLoader:
    def __init__(self, master_dir: Path = MASTER_DATA_DIR, contracts_dir: Path = CONTRACTS_DIR):
        self.master_dir = master_dir
        self.contracts_dir = contracts_dir
        self.items: Dict[str, Item] = {}
        self.suppliers: Dict[str, Supplier] = {}
        self.plants: Dict[str, Plant] = {}
        self.po_history: List[POHistoryEntry] = []
        self.contracts: Dict[str, Contract] = {}
        
        self.load_all()

    def load_all(self):
        self.load_plants()
        self.load_items()
        self.load_suppliers()
        self.load_po_history()
        self.load_contracts()

    def load_plants(self):
        f = self.master_dir / "plants.csv"
        if f.exists():
            df = pd.read_csv(f)
            for _, row in df.iterrows():
                plant_code = str(row["plant"]).strip()
                name = str(row.get("name", plant_code)).strip()
                self.plants[plant_code] = Plant(plant=plant_code, name=name)

    def load_items(self):
        f = self.master_dir / "item_master.csv"
        if f.exists():
            df = pd.read_csv(f)
            for _, row in df.iterrows():
                code = str(row["item_code"]).strip()
                self.items[code] = Item(
                    item_code=code,
                    description=str(row["description"]).strip(),
                    uom=str(row["uom"]).strip(),
                    category=str(row["category"]).strip(),
                    item_type=str(row["item_type"]).strip(),
                    standard_price=float(row["standard_price"])
                )

    def load_suppliers(self):
        f = self.master_dir / "supplier_master.csv"
        if f.exists():
            df = pd.read_csv(f)
            for _, row in df.iterrows():
                s_id = str(row["supplier_id"]).strip()
                cat_str = str(row["categories"]).strip() if pd.notna(row.get("categories")) else ""
                cats = [c.strip() for c in cat_str.split(";") if c.strip()] if cat_str else []
                self.suppliers[s_id] = Supplier(
                    supplier_id=s_id,
                    name=str(row["name"]).strip(),
                    city=str(row.get("city", "")).strip(),
                    categories=cats,
                    status=str(row["status"]).strip(),
                    on_time_pct=float(row.get("on_time_pct", 0.0)),
                    quality_rating=float(row.get("quality_rating", 0.0))
                )

    def load_po_history(self):
        f = self.master_dir / "po_history.csv"
        if f.exists():
            df = pd.read_csv(f)
            entries = []
            for _, row in df.iterrows():
                delivered_val = row.get("delivered_on_time", True)
                if isinstance(delivered_val, str):
                    delivered = delivered_val.strip().lower() in ["true", "1", "yes"]
                else:
                    delivered = bool(delivered_val)
                entries.append(POHistoryEntry(
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
            self.po_history = entries

    def load_contracts(self):
        reg_file = self.contracts_dir / "contract_register.csv"
        lines_file = self.contracts_dir / "contract_lines.csv"
        
        # Load register
        if reg_file.exists():
            df_reg = pd.read_csv(reg_file)
            for _, row in df_reg.iterrows():
                c_id = str(row["contract_id"]).strip()
                self.contracts[c_id] = Contract(
                    contract_id=c_id,
                    supplier_id=str(row["supplier_id"]).strip(),
                    supplier_name=str(row["supplier_name"]).strip(),
                    start_date=str(row["start_date"]).strip(),
                    end_date=str(row["end_date"]).strip(),
                    value_cap=float(row["value_cap"]),
                    consumed_value=float(row.get("consumed_value", 0.0)),
                    lines={},
                    is_pdf_extracted=False
                )
                
        # Load lines
        if lines_file.exists():
            df_lines = pd.read_csv(lines_file)
            for _, row in df_lines.iterrows():
                c_id = str(row["contract_id"]).strip()
                i_code = str(row["item_code"]).strip()
                rate = float(row["rate"])
                if c_id in self.contracts:
                    self.contracts[c_id].lines[i_code] = rate

        # Check PDF contracts directory for contracts that are only in PDF
        pdf_dir = self.contracts_dir / "pdf"
        if pdf_dir.exists():
            for pdf_file in pdf_dir.glob("*.pdf"):
                extracted = extract_contract_from_pdf(pdf_file)
                if extracted:
                    if extracted.contract_id not in self.contracts:
                        # Contract exists only as PDF! Section 4.4: valid from start date, consumed_value starts at 0
                        self.contracts[extracted.contract_id] = extracted
                    else:
                        # If existing contract had no lines in CSV, augment with lines from PDF
                        if not self.contracts[extracted.contract_id].lines and extracted.lines:
                            self.contracts[extracted.contract_id].lines.update(extracted.lines)

# Singleton Instance
data_loader = DataLoader()
