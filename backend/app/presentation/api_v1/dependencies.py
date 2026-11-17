from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.infrastructure.repositories.sql_repositories import (
    SQLItemRepository, SQLSupplierRepository, SQLContractRepository,
    SQLPOHistoryRepository, SQLRequirementRepository, SQLPolicyRepository,
    SQLAuditRepository
)
from app.application.use_cases.process_batch_use_case import ProcessBatchUseCase
from app.application.use_cases.chat_intake_use_case import ChatIntakeUseCase
from app.application.use_cases.apply_policy_amendment_use_case import ApplyPolicyAmendmentUseCase
from app.application.use_cases.rank_preferred_suppliers_use_case import RankPreferredSuppliersUseCase
from app.application.use_cases.buyer_actions_use_case import BuyerActionsUseCase

def get_item_repo(db: Session = Depends(get_db)) -> SQLItemRepository:
    return SQLItemRepository(db)

def get_supplier_repo(db: Session = Depends(get_db)) -> SQLSupplierRepository:
    return SQLSupplierRepository(db)

def get_contract_repo(db: Session = Depends(get_db)) -> SQLContractRepository:
    return SQLContractRepository(db)

def get_po_history_repo(db: Session = Depends(get_db)) -> SQLPOHistoryRepository:
    return SQLPOHistoryRepository(db)

def get_requirement_repo(db: Session = Depends(get_db)) -> SQLRequirementRepository:
    return SQLRequirementRepository(db)

def get_policy_repo(db: Session = Depends(get_db)) -> SQLPolicyRepository:
    return SQLPolicyRepository(db)

def get_audit_repo(db: Session = Depends(get_db)) -> SQLAuditRepository:
    return SQLAuditRepository(db)

def get_process_batch_use_case(
    item_repo: SQLItemRepository = Depends(get_item_repo),
    supplier_repo: SQLSupplierRepository = Depends(get_supplier_repo),
    contract_repo: SQLContractRepository = Depends(get_contract_repo),
    po_history_repo: SQLPOHistoryRepository = Depends(get_po_history_repo),
    requirement_repo: SQLRequirementRepository = Depends(get_requirement_repo),
    policy_repo: SQLPolicyRepository = Depends(get_policy_repo)
) -> ProcessBatchUseCase:
    return ProcessBatchUseCase(
        item_repo=item_repo,
        supplier_repo=supplier_repo,
        contract_repo=contract_repo,
        po_history_repo=po_history_repo,
        requirement_repo=requirement_repo,
        policy_repo=policy_repo
    )

def get_chat_intake_use_case(
    item_repo: SQLItemRepository = Depends(get_item_repo)
) -> ChatIntakeUseCase:
    return ChatIntakeUseCase(item_repo=item_repo)

# Singleton state for amendment use case so pending diffs persist across endpoints
_amendment_use_case_instance = None

def get_apply_amendment_use_case(
    policy_repo: SQLPolicyRepository = Depends(get_policy_repo),
    audit_repo: SQLAuditRepository = Depends(get_audit_repo)
) -> ApplyPolicyAmendmentUseCase:
    global _amendment_use_case_instance
    if _amendment_use_case_instance is None:
        _amendment_use_case_instance = ApplyPolicyAmendmentUseCase(policy_repo, audit_repo)
    else:
        _amendment_use_case_instance.policy_repo = policy_repo
        _amendment_use_case_instance.audit_repo = audit_repo
    return _amendment_use_case_instance

def get_preferred_suppliers_use_case(
    item_repo: SQLItemRepository = Depends(get_item_repo),
    supplier_repo: SQLSupplierRepository = Depends(get_supplier_repo),
    contract_repo: SQLContractRepository = Depends(get_contract_repo),
    po_history_repo: SQLPOHistoryRepository = Depends(get_po_history_repo),
    policy_repo: SQLPolicyRepository = Depends(get_policy_repo)
) -> RankPreferredSuppliersUseCase:
    return RankPreferredSuppliersUseCase(
        item_repo=item_repo,
        supplier_repo=supplier_repo,
        contract_repo=contract_repo,
        po_history_repo=po_history_repo,
        policy_repo=policy_repo
    )

def get_buyer_actions_use_case(
    requirement_repo: SQLRequirementRepository = Depends(get_requirement_repo),
    audit_repo: SQLAuditRepository = Depends(get_audit_repo)
) -> BuyerActionsUseCase:
    return BuyerActionsUseCase(
        requirement_repo=requirement_repo,
        audit_repo=audit_repo
    )
