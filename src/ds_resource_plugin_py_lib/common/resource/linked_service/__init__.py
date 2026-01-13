"""
**File:** ``__init__.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/linked_service``

Description
-----------
Linked service models and typed properties.
"""

from .base import LinkedService, LinkedServiceInfo, LinkedServiceTypedProperties

__all__ = [
    "LinkedService",
    "LinkedServiceInfo",
    "LinkedServiceTypedProperties",
]
