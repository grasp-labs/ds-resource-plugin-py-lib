"""
**File:** ``__init__.py``
**Region:** ``ds_resource_plugin_py_lib/common``

Description
-----------
Common utilities for resources and (de)serialization.
"""

from . import resource, serde

__all__ = [
    "resource",
    "serde",
]
