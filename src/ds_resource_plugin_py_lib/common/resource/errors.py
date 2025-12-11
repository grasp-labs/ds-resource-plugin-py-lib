"""
Exceptions for Resources.
"""

from typing import Any


class ResourceException(Exception):
    """Base exception for all resource-related errors."""

    def __init__(
        self,
        message: str = "Resource operation failed",
        code: str = "RESOURCE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DeserializationException(ResourceException):
    """Raised when a deserialization operation fails."""

    def __init__(
        self,
        message: str = "Deserialization operation failed",
        code: str = "DESERIALIZATION_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)
