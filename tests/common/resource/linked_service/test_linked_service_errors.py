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
            "Unsupported linked service type",
            "UNSUPPORTED_LINKED_SERVICE_TYPE",
            400,
        ),
        (
            InvalidLinkedServiceTypeException,
            "Invalid linked service type",
            "INVALID_LINKED_SERVICE_TYPE",
            400,
        ),
        (
            InvalidLinkedServiceClass,
            "Invalid linked service class",
            "INVALID_LINKED_SERVICE_CLASS",
            400,
        ),
        (
            UnsupportedAuthType,
            "Unsupported auth type",
            "UNSUPPORTED_AUTH_TYPE",
            400,
        ),
        (
            AuthenticationException,
            "Authentication failed",
            "AUTHENTICATION_FAILED",
            401,
        ),
        (
            ConnectionException,
            "Connection failed",
            "CONNECTION_FAILED",
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
