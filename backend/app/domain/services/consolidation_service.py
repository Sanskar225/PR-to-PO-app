from typing import List
from app.domain.entities.requirement import RequirementGroup
from app.domain.entities.purchase_order import ConsolidatedPurchaseOrder

class ConsolidationDomainService:
    @staticmethod
    def consolidate_purchase_orders(
        requirements: List[RequirementGroup],
        window_hours: int = 24
    ) -> List[ConsolidatedPurchaseOrder]:
        """
        Executes Policy Clause 7.1 & 7.2:
        Takes requirements in order of creation time.
        Consolidates qualifying PO requirements into multi-line POs.
        """
        open_pos: List[ConsolidatedPurchaseOrder] = []
        po_counter = 1

        for req in requirements:
            if req.decision == "PO":
                matched_po = None
                for po in open_pos:
                    if po.can_consolidate(req, window_hours=window_hours):
                        matched_po = po
                        break

                if matched_po:
                    matched_po.add_requirement(req)
                else:
                    new_po_id = f"PO-{po_counter:04d}"
                    po_counter += 1
                    new_po = ConsolidatedPurchaseOrder(
                        po_id=new_po_id,
                        supplier_id=req.supplier_id or "",
                        plant=req.plant,
                        route=req.route or "",
                        first_requirement_created_at=req.first_created_at
                    )
                    new_po.add_requirement(req)
                    open_pos.append(new_po)
            else:
                req.po_id = None

        return open_pos
