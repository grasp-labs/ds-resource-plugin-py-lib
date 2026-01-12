"""
**File:** ``errors.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/dataset``

Description
-----------
Exceptions for datasets.
"""

from typing import Any

from ..errors import ResourceException


class DatasetException(ResourceException):
    """Base exception for all dataset-related errors."""

    def __init__(
        self,
        message: str = "Dataset operation failed",
        code: str = "DS_DATASET_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class MismatchedLinkedServiceError(DatasetException):
    """Raised when a linked service does not match the dataset type."""

    def __init__(
        self,
        message: str = "Mismatched linked service",
        code: str = "DS_DATASET_LINKED_SERVICE_MISMATCHED_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class UnsupportedDatasetTypeError(DatasetException):
    """Raised when a dataset type is not supported."""

    def __init__(
        self,
        message: str = "Dataset type is not supported",
        code: str = "DS_DATASET_UNSUPPORTED_TYPE_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class InvalidDatasetClassError(DatasetException):
    """Raised when a dataset type is invalid."""

    def __init__(
        self,
        message: str = "Invalid dataset type",
        code: str = "DS_DATASET_INVALID_CLASS_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class FileNotFoundError(DatasetException):
    """Raised when file not found."""

    def __init__(
        self,
        message: str = "File not found",
        code: str = "DS_DATASET_NOT_FOUND_ERROR",
        status_code: int = 404,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class ReadError(DatasetException):
    """Raised when a read operation fails."""

    def __init__(
        self,
        message: str = "Read operation failed",
        code: str = "DS_DATASET_READ_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class WriteError(DatasetException):
    """Raised when a write operation fails."""

    def __init__(
        self,
        message: str = "Write operation failed",
        code: str = "DS_DATASET_WRITE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class UpdateError(DatasetException):
    """Raised when a update operation fails."""

    def __init__(
        self,
        message: str = "Update operation failed",
        code: str = "DS_DATASET_UPDATE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)


class DeleteError(DatasetException):
    """Raised when a delete operation fails."""

    def __init__(
        self,
        message: str = "Delete operation failed",
        code: str = "DS_DATASET_DELETE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, status_code, details)
