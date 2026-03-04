"""
**File:** ``storage_format.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/dataset``

Description
-----------
Storage format models for datasets.

Example
-------
.. code-block:: python

    from ds_resource_plugin_py_lib.common.resource.dataset.storage_format import (
        CsvFormat,
        DatasetStorageFormatType,
    )

    fmt = CsvFormat(args={"delimiter": ";"})
    assert fmt.type == DatasetStorageFormatType.CSV
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ds_common_serde_py_lib import Serializable


class DatasetStorageFormatType(StrEnum):
    """
    Enum to define the storage format types.
    """

    parquet = "parquet"
    csv = "csv"
    json = "json"
    excel = "excel"
    semi_structured_json = "semi_structured_json"
    xml = "xml"


@dataclass(kw_only=True)
class DatasetStorageFormat(Serializable):
    """
    The object containing the storage format of the dataset.
    """

    type: DatasetStorageFormatType
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class ParquetFormat(DatasetStorageFormat):
    type: DatasetStorageFormatType = DatasetStorageFormatType.parquet
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class CsvFormat(DatasetStorageFormat):
    type: DatasetStorageFormatType = DatasetStorageFormatType.csv
    args: dict[str, Any] = field(default_factory=lambda: {"delimiter": ","})


@dataclass(kw_only=True)
class SemiStructuredJsonFormat(DatasetStorageFormat):
    type: DatasetStorageFormatType = DatasetStorageFormatType.semi_structured_json
    args: dict[str, Any] = field(default_factory=lambda: {"record_path": None})


@dataclass(kw_only=True)
class XMLFormat(DatasetStorageFormat):
    type: DatasetStorageFormatType = DatasetStorageFormatType.xml
    args: dict[str, Any] = field(default_factory=dict)
