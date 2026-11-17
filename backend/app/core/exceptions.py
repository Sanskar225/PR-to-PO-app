class DomainException(Exception):
    """Base exception for all domain business rule violations."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code

class EntityNotFoundException(DomainException):
    def __init__(self, entity_name: str, identifier: str):
        super().__init__(f"{entity_name} with identifier '{identifier}' was not found.", code="NOT_FOUND")
        self.entity_name = entity_name
        self.identifier = identifier

class ContractCeilingExceededException(DomainException):
    def __init__(self, contract_id: str, requested_val: float, available_ceiling: float):
        super().__init__(
            f"Contract {contract_id} ceiling exceeded: requested ₹{requested_val:,.2f}, available headroom ₹{available_ceiling:,.2f}",
            code="CEILING_EXCEEDED"
        )
        self.contract_id = contract_id
        self.requested_val = requested_val
        self.available_ceiling = available_ceiling

class BlockedSupplierException(DomainException):
    def __init__(self, supplier_id: str):
        super().__init__(f"Supplier {supplier_id} is Blocked/Inactive and cannot participate in procurement (Policy 5.7).", code="BLOCKED_SUPPLIER")
        self.supplier_id = supplier_id

class InvalidPRLineException(DomainException):
    def __init__(self, pr_no: str, pr_line: int, reason: str):
        super().__init__(f"Invalid PR line {pr_no}/{pr_line}: {reason}", code="INVALID_PR_LINE")
        self.pr_no = pr_no
        self.pr_line = pr_line

class PolicySpecificationException(DomainException):
    def __init__(self, message: str):
        super().__init__(f"Policy specification evaluation error: {message}", code="POLICY_SPEC_ERROR")

class AmendmentParseException(DomainException):
    def __init__(self, message: str):
        super().__init__(f"Failed to parse policy amendment: {message}", code="AMENDMENT_PARSE_ERROR")
