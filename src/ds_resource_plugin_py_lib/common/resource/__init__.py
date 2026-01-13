"""
**File:** ``__init__.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource``

Description
-----------
Public resource APIs: datasets, linked services, and the resource client.
"""

from . import dataset, linked_service
from .client import ResourceClient

__all__ = [
    "ResourceClient",
    "dataset",
    "linked_service",
]
