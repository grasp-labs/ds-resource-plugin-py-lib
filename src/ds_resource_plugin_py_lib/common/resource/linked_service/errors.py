"""
**File:** ``errors.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/linked_service``

Description
-----------
Exceptions for linked services.
"""

from typing import Any

from ..errors import ResourceException


class LinkedServiceException(ResourceException):
    """Base exception for all linked service-related errors."""

    def __init__(
        self,
        message: str = "Linked service operation failed",
        code: str = "DS_LINKED_SERVICE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class UnsupportedLinkedServiceTypeError(LinkedServiceException):
    """Raised when an unsupported linked service type is provided."""

    def __init__(
        self,
        message: str = "Unsupported linked service type",
        code: str = "DS_LINKED_SERVICE_UNSUPPORTED_TYPE_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class InvalidLinkedServiceTypeError(LinkedServiceException):
    """Raised when an invalid linked service type is provided."""

    def __init__(
        self,
        message: str = "Invalid linked service type",
        code: str = "DS_LINKED_SERVICE_INVALID_TYPE_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class InvalidLinkedServiceClassError(LinkedServiceException):
    """Raised when an invalid linked service class is provided"""

    def __init__(
        self,
        message: str = "Invalid linked service class",
        code: str = "DS_LINKED_SERVICE_INVALID_CLASS_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class AuthenticationError(LinkedServiceException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "DS_LINKED_SERVICE_AUTHENTICATION_ERROR",
        status_code: int = 401,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class AuthorizationError(LinkedServiceException):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "Authorization failed",
        code: str = "DS_LINKED_SERVICE_AUTHORIZATION_ERROR",
        status_code: int = 403,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class ConnectionError(LinkedServiceException):
    """Raised when a connection fails."""

    def __init__(
        self,
        message: str = "Connection failed",
        code: str = "DS_LINKED_SERVICE_CONNECTION_ERROR",
        status_code: int = 503,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)
