"""
**File:** ``errors.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource``

Description
-----------
Exceptions for resources.
"""

from typing import Any


class ResourceException(Exception):
    """Base exception for all resource-related errors."""

    def __init__(
        self,
        message: str = "Resource operation failed",
        code: str = "DS_RESOURCE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
