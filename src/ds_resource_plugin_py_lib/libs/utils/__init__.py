"""
**File:** ``__init__.py``
**Region:** ``ds_resource_plugin_py_lib/libs/utils``

Description
-----------
Internal shared libraries used by this package (utilities).
"""

from .import_string import import_string
from .sanitize import sanitize_version

__all__ = ["import_string", "sanitize_version"]
