"""
**File:** ``enums.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/linked_service``

Description
-----------
Enumerations for linked service operations.
"""

from enum import StrEnum


class LinkedServiceMethod(StrEnum):
    """Allowed linked service operation names."""

    CONNECT = "connect"
    """Establish a connection to the backend data store."""
    TEST_CONNECTION = "test_connection"
    """Verify that the connection to the backend is healthy."""
