"""
File: test_dataset_errors.py
Description: Tests for dataset error types ensuring codes, status, and messages are preserved.
Region: packages/shared
"""

import pytest

from ds_resource_plugin_py_lib.common.resource.dataset.errors import (
    BadRequestException,
    DatasetException,
    DeleteException,
    FileNotFound,
    InvalidDatasetClass,
    JsonDecodeException,
    MismatchedLinkedServiceException,
    ReadException,
    UnsupportedDatasetType,
    UpdateException,
    WriteException,
)


@pytest.mark.parametrize(
    ("exc_cls", "expected_code", "expected_status", "expected_message"),
    [
        (DatasetException, "DATASET_ERROR", 500, "Dataset operation failed"),
        (MismatchedLinkedServiceException, "MISMATCHED_LINKED_SERVICE", 400, "Mismatched linked service"),
        (UnsupportedDatasetType, "UNSUPPORTED_DATASET_TYPE", 400, "Dataset type is not supported"),
        (InvalidDatasetClass, "INVALID_DATASET_TYPE", 400, "Invalid dataset type"),
        (FileNotFound, "NOT_FOUND", 404, "File not found"),
        (WriteException, "WRITE_ERROR", 500, "Write operation failed"),
        (UpdateException, "UPDATE_ERROR", 500, "Update operation failed"),
        (ReadException, "READ_ERROR", 500, "Read operation failed"),
        (DeleteException, "DELETE_ERROR", 500, "Delete operation failed"),
        (JsonDecodeException, "JSON_DECODE_ERROR", 400, "Failed to decode JSON."),
        (BadRequestException, "BAD_REQUEST", 400, "Bad Request."),
    ],
)
def test_dataset_exception_defaults(exc_cls, expected_code, expected_status, expected_message):
    """Validate default code, status_code, message, and details."""
    exc = exc_cls()

    assert exc.code == expected_code
    assert exc.status_code == expected_status
    assert exc.message == expected_message
    assert exc.details == {}
    assert str(exc) == expected_message


def test_dataset_exception_custom_details():
    """Ensure details propagate when provided."""
    details = {"context": "extra"}
    exc = DatasetException(message="custom", code="CUSTOM", status_code=418, details=details)

    assert exc.details == details
    assert exc.code == "CUSTOM"
    assert exc.status_code == 418
    assert str(exc) == "custom"
