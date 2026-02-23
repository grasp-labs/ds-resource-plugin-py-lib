"""
**File:** ``__init__.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/linked_service``

Description
-----------
Linked service models and typed properties.
"""

from .base import LinkedService, LinkedServiceInfo, LinkedServiceSettings
from .enums import LinkedServiceMethod

__all__ = [
    "LinkedService",
    "LinkedServiceInfo",
    "LinkedServiceMethod",
    "LinkedServiceSettings",
]
