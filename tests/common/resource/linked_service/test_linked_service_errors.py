"""
**File:** ``test_linked_service_errors.py``
**Region:** ``tests/common/resource/linked_service``

Description
-----------
Tests for linked service error types ensuring codes, status, and messages are preserved.
"""

import pytest

from ds_resource_plugin_py_lib.common.resource.linked_service.errors import (
    AuthenticationError,
    ConnectionError,
    InvalidLinkedServiceClassError,
    InvalidLinkedServiceTypeError,
    LinkedServiceException,
    UnsupportedLinkedServiceTypeError,
)


@pytest.mark.parametrize(
    ("exc_cls", "expected_code", "expected_message", "expected_status"),
    [
        (
            LinkedServiceException,
            "DS_LINKED_SERVICE_ERROR",
            "Linked service operation failed",
            500,
        ),
        (
            UnsupportedLinkedServiceTypeError,
            "DS_LINKED_SERVICE_UNSUPPORTED_TYPE_ERROR",
            "Unsupported linked service type",
            400,
        ),
        (
            InvalidLinkedServiceTypeError,
            "DS_LINKED_SERVICE_INVALID_TYPE_ERROR",
            "Invalid linked service type",
            400,
        ),
        (
            InvalidLinkedServiceClassError,
            "DS_LINKED_SERVICE_INVALID_CLASS_ERROR",
            "Invalid linked service class",
            400,
        ),
        (
            AuthenticationError,
            "DS_LINKED_SERVICE_AUTHENTICATION_ERROR",
            "Authentication failed",
            401,
        ),
        (
            ConnectionError,
            "DS_LINKED_SERVICE_CONNECTION_ERROR",
            "Connection failed",
            503,
        ),
    ],
)
def test_linked_service_exception_defaults(exc_cls, expected_code, expected_message, expected_status):
    """Validate current default code/message wiring and details."""
    exc = exc_cls()

    assert exc.code == expected_code
    assert exc.status_code == expected_status
    assert exc.message == expected_message
    assert exc.details == {}
    assert str(exc) == expected_message


def test_linked_service_exception_custom_details():
    """Ensure details propagate when provided."""
    details = {"cause": "timeout"}
    exc = LinkedServiceException(message="custom", code="CUSTOM", status_code=410, details=details)

    assert exc.details == details
    assert exc.code == "CUSTOM"
    assert exc.status_code == 410
    assert str(exc) == "custom"
