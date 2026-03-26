"""
**File:** ``base.py``
**Region:** ``ds_resource_plugin_py_lib/common/serde``

Description
-----------
Shared serde configuration models.
"""

from dataclasses import dataclass, field
from typing import Any

from ds_common_serde_py_lib import Serializable

from ..resource.dataset.storage_format import DatasetStorageFormatType


@dataclass(kw_only=True)
class SerdeSettings(Serializable):
    """Base class for static serde configuration."""


@dataclass(kw_only=True)
class DataFrameSerdeSettings(SerdeSettings):
    """Static configuration shared by DataFrame-oriented serde classes."""

    format: DatasetStorageFormatType
    kwargs: dict[str, Any] = field(default_factory=dict)
