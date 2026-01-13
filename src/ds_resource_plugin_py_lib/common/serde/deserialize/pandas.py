"""
**File:** ``pandas.py``
**Region:** ``ds_resource_plugin_py_lib/common/serde/deserialize``

Description
-----------
Deserialize a value into a pandas DataFrame.

Example
-------
.. code-block:: python

    from ds_resource_plugin_py_lib.common.resource.dataset.storage_format import DatasetStorageFormatType
    from ds_resource_plugin_py_lib.common.serde.deserialize.pandas import PandasDeserializer

    deserializer = PandasDeserializer(format=DatasetStorageFormatType.JSON)
    df = deserializer('{"a":[1,2],"b":["x","y"]}')
"""

import io
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

import pandas as pd

from ....common.resource.dataset.storage_format import DatasetStorageFormatType
from ...serde.deserialize.base import DataDeserializer


@dataclass(kw_only=True)
class PandasDeserializer(DataDeserializer):
    format: DatasetStorageFormatType
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __call__(self, value: Any, **_kwargs: Any) -> pd.DataFrame:
        """
        Deserialize a value into a pandas DataFrame.
        Args:
            value: The value to deserialize.
            **kwargs: Additional keyword arguments.
        Returns:
            A pandas DataFrame.
        """
        self.log.info(f"PandasDeserializer __call__ with format: {self.format} and args: {self.kwargs}")

        if isinstance(value, bytes):
            value = io.BytesIO(value)
        elif isinstance(value, str):
            value = io.StringIO(value)
        elif isinstance(value, (dict, list)):
            value = json.dumps(value)

        format_readers: dict[DatasetStorageFormatType, Callable[[Any], pd.DataFrame]] = {
            DatasetStorageFormatType.CSV: lambda v: pd.read_csv(v, **self.kwargs),
            DatasetStorageFormatType.PARQUET: lambda v: pd.read_parquet(v, **self.kwargs),
            DatasetStorageFormatType.JSON: lambda v: pd.read_json(v, **self.kwargs),
            DatasetStorageFormatType.EXCEL: lambda v: pd.read_excel(v, **self.kwargs),
            DatasetStorageFormatType.XML: lambda v: pd.read_xml(v, **self.kwargs),
        }

        if self.format == DatasetStorageFormatType.SEMI_STRUCTURED_JSON:
            if isinstance(value, io.BytesIO):
                json_str = value.getvalue().decode("utf-8")
                value = json.loads(json_str)
            elif isinstance(value, io.StringIO):
                json_str = value.getvalue()
                value = json.loads(json_str)
            elif isinstance(value, str):
                value = json.loads(value)
            return pd.json_normalize(value, **self.kwargs)

        reader = format_readers.get(self.format)
        if reader:
            return reader(value)

        raise ValueError(f"Unsupported format: {self.format}")
