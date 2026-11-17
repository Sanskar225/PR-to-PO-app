from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.domain.entities.item import Item
from app.domain.entities.supplier import Supplier
from app.domain.entities.contract import RateContract
from app.domain.entities.requirement import RequirementGroup
from app.domain.policies.policy_document import PolicyDocumentAggregate

class IItemRepository(ABC):
    @abstractmethod
    def get_by_code(self, item_code: str) -> Optional[Item]:
        pass

    @abstractmethod
    def get_all(self) -> List[Item]:
        pass

    @abstractmethod
    def get_all_indexed(self) -> Dict[str, Item]:
        pass

class ISupplierRepository(ABC):
    @abstractmethod
    def get_by_id(self, supplier_id: str) -> Optional[Supplier]:
        pass

    @abstractmethod
    def get_all(self) -> List[Supplier]:
        pass

    @abstractmethod
    def get_all_active(self) -> List[Supplier]:
        pass

class IContractRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[RateContract]:
        pass

    @abstractmethod
    def get_contracts_covering_item(self, item_code: str) -> List[RateContract]:
        pass

    @abstractmethod
    def save(self, contract: RateContract) -> None:
        pass

class IPOHistoryRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Any]:
        pass

    @abstractmethod
    def get_by_item(self, item_code: str) -> List[Any]:
        pass

class IRequirementRepository(ABC):
    @abstractmethod
    def save_batch_results(
        self,
        batch_id: str,
        filename: str,
        requirements: List[RequirementGroup]
    ) -> None:
        pass

    @abstractmethod
    def get_all_requirements(self) -> List[RequirementGroup]:
        pass

    @abstractmethod
    def get_by_group_id(self, group_id: str) -> Optional[RequirementGroup]:
        pass

    @abstractmethod
    def update_requirement(self, requirement: RequirementGroup) -> None:
        pass

class IPolicyRepository(ABC):
    @abstractmethod
    def get_active_policy(self) -> PolicyDocumentAggregate:
        pass

    @abstractmethod
    def get_by_version(self, version: str) -> Optional[PolicyDocumentAggregate]:
        pass

    @abstractmethod
    def get_all_versions(self) -> List[str]:
        pass

    @abstractmethod
    def save_version(self, policy: PolicyDocumentAggregate) -> None:
        pass

    @abstractmethod
    def set_active_version(self, version: str) -> None:
        pass

class IAuditRepository(ABC):
    @abstractmethod
    def record_audit(
        self,
        group_id: Optional[str],
        actor: str,
        action: str,
        details: str,
        comment: Optional[str] = None,
        override_route: Optional[str] = None,
        override_supplier_id: Optional[str] = None
    ) -> None:
        pass

    @abstractmethod
    def get_all_logs(self) -> List[Dict[str, Any]]:
        pass
