"""Domain exceptions for CLIMORA Service Boundary.

These exceptions map to standard API error codes and clean, un-leaked responses.
"""

from typing import Any, Dict, Optional


class ClimoraServiceError(Exception):
    """Base exception for all domain service errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code


class ProjectNotFoundError(ClimoraServiceError):
    """Raised when a requested project ID is not found in the project registry."""

    def __init__(self, project_id: str):
        super().__init__(
            message=f"Project '{project_id}' not found.",
            code="PROJECT_NOT_FOUND",
            details={"requested_project_id": project_id},
            status_code=404,
        )


class AllocationImmutableError(ClimoraServiceError):
    """Raised when an attempt is made to directly mutate or overwrite canonical optimization allocations."""

    def __init__(self, message: str = "Canonical optimization allocation is read-only and immutable."):
        super().__init__(
            message=message,
            code="ALLOCATION_IMMUTABLE",
            details={"action_permitted": "Propose an auditable revision via /revisions"},
            status_code=405,
        )


class StateTransitionError(ClimoraServiceError):
    """Raised when an illegal project lifecycle transition is attempted."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ILLEGAL_STATE_TRANSITION",
            details=details or {},
            status_code=422,
        )


class VerificationNotEligibleError(ClimoraServiceError):
    """Raised when verification prerequisites are unsatisfied or synthetic data is rejected."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VERIFICATION_NOT_ELIGIBLE",
            details=details or {},
            status_code=422,
        )


class ValidationError(ClimoraServiceError):
    """Raised when an incoming operational payload fails domain-level validation."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details or {},
            status_code=400,
        )
