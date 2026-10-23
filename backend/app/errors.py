"""Error classes and standard error code constants for MuleNet API."""

from typing import Any, Optional

ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
NOT_FOUND = "NOT_FOUND"
METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
VALIDATION_ERROR = "VALIDATION_ERROR"
INVALID_BUDGET = "INVALID_BUDGET"
INVALID_HOPS = "INVALID_HOPS"
INVALID_MAX_NODES = "INVALID_MAX_NODES"
ARTIFACTS_NOT_FOUND = "ARTIFACTS_NOT_FOUND"
INTERNAL_ERROR = "INTERNAL_ERROR"
NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class APIError(Exception):
    """Base API exception that translates into standardized error envelopes."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
