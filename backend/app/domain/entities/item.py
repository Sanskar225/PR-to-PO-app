from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ItemType(str, Enum):
    MATERIAL = "Material"
    CAPEX = "Capex"
    SERVICE = "Service"
    CONSUMABLE = "Consumable"
    UNKNOWN = "Unknown"

    @classmethod
    def from_str(cls, val: str) -> "ItemType":
        if not val:
            return cls.UNKNOWN
        clean = val.strip().lower()
        if "capex" in clean:
            return cls.CAPEX
        elif "service" in clean:
            return cls.SERVICE
        elif "material" in clean:
            return cls.MATERIAL
        elif "consumable" in clean:
            return cls.CONSUMABLE
        return cls.UNKNOWN

@dataclass(frozen=True)
class Item:
    item_code: str
    description: str
    uom: str
    category: str
    item_type: ItemType
    standard_price: float

    @property
    def is_capex(self) -> bool:
        return self.item_type == ItemType.CAPEX
