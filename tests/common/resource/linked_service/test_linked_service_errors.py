"""
File: test_linked_service_errors.py
Description: Tests for linked service error types ensuring codes, status, and messages are preserved.
Region: packages/shared
"""

import pytest

from ds_resource_plugin_py_lib.common.resource.linked_service.errors import (
    AuthenticationException,
    ConnectionException,
    InvalidLinkedServiceClass,
    InvalidLinkedServiceTypeException,
    LinkedServiceException,
    UnsupportedAuthType,
    UnsupportedLinkedServiceType,
)


@pytest.mark.parametrize(
    ("exc_cls", "expected_code", "expected_message", "expected_status"),
    [
        (
            LinkedServiceException,
            "LINKED_SERVICE_ERROR",
            "Linked service operation failed",
            500,
        ),
        (
            UnsupportedLinkedServiceType,
            "UNSUPPORTED_LINKED_SERVICE_TYPE",
            "Unsupported linked service type",
            400,
        ),
        (
            InvalidLinkedServiceTypeException,
            "INVALID_LINKED_SERVICE_TYPE",
            "Invalid linked service type",
            400,
        ),
        (
            InvalidLinkedServiceClass,
            "INVALID_LINKED_SERVICE_CLASS",
            "Invalid linked service class",
            400,
        ),
        (
            UnsupportedAuthType,
            "UNSUPPORTED_AUTH_TYPE",
            "Unsupported auth type",
            400,
        ),
        (
            AuthenticationException,
            "AUTHENTICATION_FAILED",
            "Authentication failed",
            401,
        ),
        (
            ConnectionException,
            "CONNECTION_FAILED",
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
