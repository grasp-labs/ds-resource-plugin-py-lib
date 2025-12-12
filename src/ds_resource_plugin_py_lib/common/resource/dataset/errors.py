"""
Exceptions for Datasets.
"""

from typing import Any

from ..errors import ResourceException


class DatasetException(ResourceException):
    """Base exception for all dataset-related errors."""

    def __init__(
        self,
        message: str = "Dataset operation failed",
        code: str = "DATASET_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class MismatchedLinkedServiceException(DatasetException):
    """Raised when a linked service does not match the dataset type."""

    def __init__(
        self,
        message: str = "Mismatched linked service",
        code: str = "MISMATCHED_LINKED_SERVICE",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class UnsupportedDatasetType(DatasetException):
    """Raised when a dataset type is not supported."""

    def __init__(
        self,
        message: str = "Dataset type is not supported",
        code: str = "UNSUPPORTED_DATASET_TYPE",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class InvalidDatasetClass(DatasetException):
    """Raised when a dataset type is invalid."""

    def __init__(
        self,
        message: str = "Invalid dataset type",
        code: str = "INVALID_DATASET_TYPE",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class FileNotFound(DatasetException):
    """Raised when file not found."""

    def __init__(
        self,
        message: str = "File not found",
        code: str = "NOT_FOUND",
        status_code: int = 404,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class WriteException(DatasetException):
    """Raised when a write operation fails."""

    def __init__(
        self,
        message: str = "Write operation failed",
        code: str = "WRITE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class UpdateException(DatasetException):
    """Raised when a update operation fails."""

    def __init__(
        self,
        message: str = "Update operation failed",
        code: str = "UPDATE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class ReadException(DatasetException):
    """Raised when a read operation fails."""

    def __init__(
        self,
        message: str = "Read operation failed",
        code: str = "READ_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class DeleteException(DatasetException):
    """Raised when a delete operation fails."""

    def __init__(
        self,
        message: str = "Delete operation failed",
        code: str = "DELETE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class JsonDecodeException(DatasetException):
    """Raised when a operation fails due to JSONDecodeError."""

    def __init__(
        self,
        message: str = "Failed to decode JSON.",
        code: str = "JSON_DECODE_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class BadRequestException(DatasetException):
    """Raised when an operation fails due to invalid input."""

    def __init__(
        self,
        message: str = "Bad Request.",
        code: str = "BAD_REQUEST",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)
