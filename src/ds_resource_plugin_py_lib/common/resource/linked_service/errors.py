"""
Exceptions for Linked Services.
"""

from typing import Any

from ..errors import ResourceException


class LinkedServiceException(ResourceException):
    """Base exception for all linked service-related errors."""

    def __init__(
        self,
        code: str = "LINKED_SERVICE_ERROR",
        message: str = "Linked service operation failed",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class UnsupportedLinkedServiceType(LinkedServiceException):
    """Raised when an unsupported linked service type is provided."""

    def __init__(
        self,
        message: str = "Unsupported linked service type",
        code: str = "UNSUPPORTED_LINKED_SERVICE_TYPE",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class InvalidLinkedServiceTypeException(LinkedServiceException):
    """Raised when an invalid linked service type is provided."""

    def __init__(
        self,
        message: str = "Invalid linked service type",
        code: str = "INVALID_LINKED_SERVICE_TYPE",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class InvalidLinkedServiceClass(LinkedServiceException):
    """Raised when an invalid linked service class is provided"""

    def __init__(
        self,
        message: str = "Invalid linked service class",
        code: str = "INVALID_LINKED_SERVICE_CLASS",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class UnsupportedAuthType(LinkedServiceException):
    """Raised when an unsupported auth type is provided."""

    def __init__(
        self,
        message: str = "Unsupported auth type",
        code: str = "UNSUPPORTED_AUTH_TYPE",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class AuthenticationException(LinkedServiceException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "AUTHENTICATION_FAILED",
        status_code: int = 401,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class ConnectionException(LinkedServiceException):
    """Raised when a connection fails."""

    def __init__(
        self,
        message: str = "Connection failed",
        code: str = "CONNECTION_FAILED",
        status_code: int = 503,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)
