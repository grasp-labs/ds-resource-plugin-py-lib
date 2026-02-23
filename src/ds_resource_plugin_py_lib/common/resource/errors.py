"""
**File:** ``errors.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource``

Description
-----------
Exceptions for resources.
"""

from typing import Any


class ResourceException(Exception):
    """Base exception for all resource-related errors."""

    def __init__(
        self,
        message: str = "Resource operation failed",
        code: str = "DS_RESOURCE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NotSupportedError(ResourceException):
    """Raised when a provider does not support an optional method."""

    def __init__(
        self,
        message: str = "Operation not supported",
        code: str = "DS_RESOURCE_NOT_SUPPORTED_ERROR",
        status_code: int = 501,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class ValidationError(ResourceException):
    """Raised when input fails validation before reaching the backend."""

    def __init__(
        self,
        message: str = "Validation failed",
        code: str = "DS_RESOURCE_VALIDATION_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)
