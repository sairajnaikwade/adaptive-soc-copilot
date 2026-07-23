"""
Custom exception hierarchy for Adaptive SOC CoPilot.

All domain exceptions inherit from SOCCopilotException so that the global
exception handler in main.py can catch them uniformly and convert them into
appropriate HTTP error responses.

Exception → HTTP Status mapping:
    AuthenticationError     → 401 Unauthorized
    AuthorizationError      → 403 Forbidden
    InvalidTokenError       → 401 Unauthorized
    ResourceNotFoundError   → 404 Not Found
    DuplicateResourceError  → 409 Conflict
    ValidationError         → 422 Unprocessable Entity
    ServiceUnavailableError → 503 Service Unavailable
"""

from typing import Any, Optional


class SOCCopilotException(Exception):
    """
    Base exception for all SOC CoPilot domain errors.

    Provides a consistent interface for attaching a human-readable message
    and an optional machine-readable detail dictionary.
    """

    def __init__(self, message: str, detail: Optional[Any] = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


# ---------------------------------------------------------------------------
# Authentication & Authorization
# ---------------------------------------------------------------------------

class AuthenticationError(SOCCopilotException):
    """
    Raised when a user cannot be authenticated.

    Examples: wrong password, account disabled, missing credentials.
    Maps to HTTP 401 Unauthorized.
    """


class InvalidTokenError(SOCCopilotException):
    """
    Raised when a JWT token is expired, malformed, or has an invalid signature.

    Maps to HTTP 401 Unauthorized.
    """


class AuthorizationError(SOCCopilotException):
    """
    Raised when an authenticated user lacks permission for an action.

    Examples: an analyst attempting an admin-only operation.
    Maps to HTTP 403 Forbidden.
    """


class InvalidCredentialsError(AuthenticationError):
    """
    Raised when email/password combination is incorrect.

    Kept as a subclass of AuthenticationError so it maps to HTTP 401.
    The message intentionally does not reveal which field is wrong.
    """


# ---------------------------------------------------------------------------
# Resource management
# ---------------------------------------------------------------------------

class ResourceNotFoundError(SOCCopilotException):
    """
    Raised when a requested resource does not exist or does not belong to
    the requesting tenant.

    Maps to HTTP 404 Not Found.
    """

    def __init__(self, resource: str, resource_id: Any) -> None:
        message = f"{resource} with id '{resource_id}' was not found."
        super().__init__(message=message, detail={"resource": resource, "id": str(resource_id)})


class DuplicateResourceError(SOCCopilotException):
    """
    Raised when a create operation would violate a uniqueness constraint.

    Examples: duplicate email in the same tenant, duplicate tenant slug.
    Maps to HTTP 409 Conflict.
    """


# ---------------------------------------------------------------------------
# Data validation
# ---------------------------------------------------------------------------

class ValidationError(SOCCopilotException):
    """
    Raised when business-logic validation fails (distinct from Pydantic
    schema validation which FastAPI handles automatically).

    Maps to HTTP 422 Unprocessable Entity.
    """


# ---------------------------------------------------------------------------
# External services
# ---------------------------------------------------------------------------

class ServiceUnavailableError(SOCCopilotException):
    """
    Raised when an external dependency (database, email server, ML service)
    is temporarily unavailable.

    Maps to HTTP 503 Service Unavailable.
    """


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

class TenantNotFoundError(ResourceNotFoundError):
    """Raised when the tenant specified in a JWT claim no longer exists."""

    def __init__(self, tenant_id: Any) -> None:
        super().__init__(resource="Tenant", resource_id=tenant_id)


class TenantMismatchError(AuthorizationError):
    """
    Raised when a request attempts to access data belonging to a different
    tenant than the one encoded in the requesting user's JWT.
    """
