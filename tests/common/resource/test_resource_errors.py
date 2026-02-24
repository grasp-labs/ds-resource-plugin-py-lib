"""
**File:** ``test_resource_errors.py``
**Region:** ``tests/common/resource``

Description
-----------
Tests for resource-level error types ensuring codes, status, and messages are preserved.
"""

import pytest

from ds_resource_plugin_py_lib.common.resource.errors import (
    NotSupportedError,
    ResourceException,
    ValidationError,
)


@pytest.mark.parametrize(
    ("exc_cls", "expected_code", "expected_status", "expected_message"),
    [
        (ResourceException, "DS_RESOURCE_ERROR", 500, "Resource operation failed"),
        (NotSupportedError, "DS_RESOURCE_NOT_SUPPORTED_ERROR", 501, "Operation not supported"),
        (ValidationError, "DS_RESOURCE_VALIDATION_ERROR", 400, "Validation failed"),
    ],
)
def test_resource_exception_defaults(exc_cls, expected_code, expected_status, expected_message):
    """Validate default code, status_code, message, and details."""
    exc = exc_cls()

    assert exc.code == expected_code
    assert exc.status_code == expected_status
    assert exc.message == expected_message
    assert exc.details == {}
    assert str(exc) == expected_message


def test_resource_exception_custom_details():
    """Ensure details propagate when provided."""
    details = {"field": "name", "reason": "missing"}
    exc = ValidationError(message="Missing column", details=details)

    assert exc.details == details
    assert exc.message == "Missing column"
    assert str(exc) == "Missing column"


def test_not_supported_error_inherits_from_resource_exception():
    """NotSupportedError must be catchable via ResourceException."""
    with pytest.raises(ResourceException):
        raise NotSupportedError()


def test_validation_error_inherits_from_resource_exception():
    """ValidationError must be catchable via ResourceException."""
    with pytest.raises(ResourceException):
        raise ValidationError()
