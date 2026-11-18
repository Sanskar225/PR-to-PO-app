from datetime import datetime, date
from typing import Union
from dateutil import parser

def parse_dt(val: Union[str, datetime, date]) -> datetime:
    """
    Robustly parses any date/datetime representation into a datetime object.
    Handles ISO 8601, 'YYYY-MM-DD HH:MM', 'YYYY-MM-DDTHH:MM:SS', 'DD/MM/YYYY', etc.
    """
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)
    
    s = str(val).strip()
    if not s or s.lower() in ["none", "nan", "nat"]:
        return datetime.utcnow()
    
    # Fast path for standard YYYY-MM-DD HH:MM or ISO
    try:
        clean = s.replace("T", " ")
        if len(clean) >= 16:
            return datetime.strptime(clean[:16], "%Y-%m-%d %H:%M")
        elif len(clean) >= 10:
            return datetime.strptime(clean[:10], "%Y-%m-%d")
    except Exception:
        pass
    
    # Fallback to dateutil parser
    try:
        return parser.parse(s)
    except Exception:
        return datetime.utcnow()

def parse_d(val: Union[str, datetime, date]) -> date:
    """
    Robustly parses any date/datetime representation into a date object.
    """
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    
    s = str(val).strip()
    if not s or s.lower() in ["none", "nan", "nat"]:
        return date.today()
    
    # Fast path for standard YYYY-MM-DD
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        pass
    
    # Fallback to dateutil parser
    try:
        return parser.parse(s).date()
    except Exception:
        return date.today()
