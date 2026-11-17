from typing import List
from app.domain.entities.pr_line import PurchaseRequisitionLine
from app.domain.entities.requirement import RequirementGroup

class ClubbingDomainService:
    @staticmethod
    def club_pr_lines(
        pr_lines: List[PurchaseRequisitionLine],
        creation_window_days: int = 14,
        need_by_window_days: int = 7
    ) -> List[RequirementGroup]:
        """
        Executes Policy Clause 2.1 & 2.2:
        Takes PR lines sorted by creation time (then PR number, then line number).
        Clubs into RequirementGroup aggregates respecting anti-splitting invariants.
        """
        # Sort lines chronologically
        sorted_lines = sorted(
            pr_lines,
            key=lambda p: (p.created_at, p.pr_no, p.pr_line)
        )

        groups: List[RequirementGroup] = []
        group_seq = 1

        for line in sorted_lines:
            joined = False
            # Clause 1.2: NEW items are never clubbed
            if not line.is_new_item:
                for g in groups:
                    if g.can_absorb(line, creation_window_days, need_by_window_days):
                        g.add_line(line)
                        joined = True
                        break

            if not joined:
                gid = f"REQ-{group_seq:04d}"
                group_seq += 1
                new_group = RequirementGroup(
                    group_id=gid,
                    resolved_item_code=line.resolved_item_code or "NEW",
                    plant=line.plant,
                    first_pr=line
                )
                groups.append(new_group)

        # Requirements processed in order of requirement date (Clause 4.2)
        groups.sort(key=lambda g: g.first_created_at)
        return groups
