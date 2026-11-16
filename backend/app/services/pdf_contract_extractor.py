import re
from pathlib import Path
from typing import Optional, Dict, Any, List
import pypdf
from app.models.schemas import Contract

def extract_contract_from_pdf(pdf_path: Path) -> Optional[Contract]:
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        full_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += "\n" + t
        
        # 1. Contract No
        contract_no_m = re.search(r"Contract\s+No\.?\s*([A-Z0-9\-]+)", full_text, re.IGNORECASE)
        contract_id = contract_no_m.group(1).strip() if contract_no_m else pdf_path.stem
        
        # 2. Supplier ID & Name
        # e.g., '... between Corvo Engineering ... and Pneumatic Point, Pune (Supplier ID S021)'
        supplier_id_m = re.search(r"Supplier\s+ID\s*[:\-]?\s*([A-Z0-9]+)", full_text, re.IGNORECASE)
        supplier_id = supplier_id_m.group(1).strip() if supplier_id_m else "UNKNOWN"
        
        # Supplier name can be extracted before "(Supplier ID" or from between ... and ...
        supp_name_m = re.search(r"and\s+([A-Za-z0-9\s\.\,\-]+?)\s*\(\s*Supplier\s+ID", full_text, re.IGNORECASE)
        supplier_name = supp_name_m.group(1).strip() if supp_name_m else "Supplier " + supplier_id
        # clean any city suffix like ", Pune"
        if "," in supplier_name:
            supplier_name = supplier_name.split(",")[0].strip()
            
        # 3. Term / Dates
        # e.g., 'valid from 2026-11-15 to 2027-11-14'
        term_m = re.search(r"valid\s+from\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*to\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", full_text, re.IGNORECASE)
        if term_m:
            start_date = term_m.group(1).strip()
            end_date = term_m.group(2).strip()
        else:
            start_date = "2026-01-01"
            end_date = "2027-12-31"
            
        # 4. Value ceiling
        # e.g., 'INR 20,00,000' or 'INR 50,00,000'
        cap_m = re.search(r"INR\s*([0-9\,]+)", full_text, re.IGNORECASE)
        if cap_m:
            cap_str = cap_m.group(1).replace(",", "").strip()
            value_cap = float(cap_str)
        else:
            value_cap = 10000000.0
            
        # 5. Schedule A: Items and rates
        # Matches lines like:
        # 1 ITM-1036 Pneumatic cylinder 50x100 NOS 3,537.76
        # ITM-1037 Solenoid valve 5/2 1/4 inch NOS 2,439.01
        lines_dict: Dict[str, float] = {}
        for line in full_text.splitlines():
            line = line.strip()
            item_match = re.search(r"(ITM-\d{4})\s+(.+?)\s+([A-Z]{2,4})\s+([\d,]+\.?\d*)", line)
            if item_match:
                item_code = item_match.group(1).strip()
                rate_str = item_match.group(4).replace(",", "").strip()
                try:
                    lines_dict[item_code] = float(rate_str)
                except ValueError:
                    pass
                    
        return Contract(
            contract_id=contract_id,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            start_date=start_date,
            end_date=end_date,
            value_cap=value_cap,
            consumed_value=0.0, # Starts at 0 for new PDF contracts
            lines=lines_dict,
            is_pdf_extracted=True
        )
    except Exception as e:
        print(f"Error extracting contract from {pdf_path}: {e}")
        return None
