import re
from pathlib import Path
from datetime import date
from typing import Optional, Dict
import pypdf
from app.domain.entities.contract import RateContract
from app.core.logging import logger

class PDFContractParser:
    @staticmethod
    def parse_pdf(pdf_path: Path) -> Optional[RateContract]:
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            full_text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    full_text += "\n" + t

            # 1. Contract No
            c_no_m = re.search(r"Contract\s+No\.?\s*([A-Z0-9\-]+)", full_text, re.IGNORECASE)
            contract_id = c_no_m.group(1).strip() if c_no_m else pdf_path.stem

            # 2. Supplier ID & Name
            s_id_m = re.search(r"Supplier\s+ID\s*[:\-]?\s*([A-Z0-9]+)", full_text, re.IGNORECASE)
            supplier_id = s_id_m.group(1).strip() if s_id_m else "UNKNOWN"

            name_m = re.search(r"and\s+([A-Za-z0-9\s\.\,\-]+?)\s*\(\s*Supplier\s+ID", full_text, re.IGNORECASE)
            supplier_name = name_m.group(1).strip() if name_m else "Supplier " + supplier_id
            if "," in supplier_name:
                supplier_name = supplier_name.split(",")[0].strip()

            # 3. Dates
            term_m = re.search(r"valid\s+from\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*to\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", full_text, re.IGNORECASE)
            if term_m:
                start_date = date.fromisoformat(term_m.group(1).strip())
                end_date = date.fromisoformat(term_m.group(2).strip())
            else:
                start_date = date(2026, 1, 1)
                end_date = date(2027, 12, 31)

            # 4. Ceiling
            cap_m = re.search(r"INR\s*([0-9\,]+)", full_text, re.IGNORECASE)
            value_cap = float(cap_m.group(1).replace(",", "").strip()) if cap_m else 10000000.0

            # 5. Schedule of rates
            lines: Dict[str, float] = {}
            for line in full_text.splitlines():
                line = line.strip()
                item_match = re.search(r"(ITM-\d{4})\s+(.+?)\s+([A-Z]{2,4})\s+([\d,]+\.?\d*)", line)
                if item_match:
                    code = item_match.group(1).strip()
                    rate = float(item_match.group(4).replace(",", "").strip())
                    lines[code] = rate

            return RateContract(
                contract_id=contract_id,
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                start_date=start_date,
                end_date=end_date,
                value_cap=value_cap,
                consumed_value=0.0, # Policy 4.2: New contracts signed after register update start at 0
                rates=lines,
                is_pdf_extracted=True
            )
        except Exception as e:
            logger.error(f"Error parsing PDF contract at {pdf_path}: {e}")
            return None
