"""
**File:** ``test_dataset_errors.py``
**Region:** ``tests/common/resource/dataset``

Description
-----------
Tests for dataset error types ensuring codes, status, and messages are preserved.
"""

import pytest

from ds_resource_plugin_py_lib.common.resource.dataset.errors import (
    DatasetException,
    DeleteError,
    FileNotFoundError,
    InvalidDatasetClassError,
    MismatchedLinkedServiceError,
    ReadError,
    UnsupportedDatasetTypeError,
    UpdateError,
    WriteError,
)


@pytest.mark.parametrize(
    ("exc_cls", "expected_code", "expected_status", "expected_message"),
    [
        (DatasetException, "DS_DATASET_ERROR", 500, "Dataset operation failed"),
        (MismatchedLinkedServiceError, "DS_DATASET_LINKED_SERVICE_MISMATCHED_ERROR", 400, "Mismatched linked service"),
        (UnsupportedDatasetTypeError, "DS_DATASET_UNSUPPORTED_TYPE_ERROR", 400, "Dataset type is not supported"),
        (InvalidDatasetClassError, "DS_DATASET_INVALID_CLASS_ERROR", 400, "Invalid dataset type"),
        (FileNotFoundError, "DS_DATASET_NOT_FOUND_ERROR", 404, "File not found"),
        (WriteError, "DS_DATASET_WRITE_ERROR", 500, "Write operation failed"),
        (UpdateError, "DS_DATASET_UPDATE_ERROR", 500, "Update operation failed"),
        (DeleteError, "DS_DATASET_DELETE_ERROR", 500, "Delete operation failed"),
        (ReadError, "DS_DATASET_READ_ERROR", 500, "Read operation failed"),
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
