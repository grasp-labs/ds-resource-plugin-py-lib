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
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ds_common_logger_py_lib import Logger

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

import pandas as pd

from ....common.resource.dataset.storage_format import DatasetStorageFormatType
from ...serde.deserialize.base import DataDeserializer
from ..base import DataFrameSerdeSettings

logger = Logger.get_logger(__name__, package=True)


@dataclass(kw_only=True)
class PandasDeserializer(DataDeserializer):
    settings: DataFrameSerdeSettings

    def __init__(
        self,
        *,
        settings: DataFrameSerdeSettings | dict[str, Any] | None = None,
        format: DatasetStorageFormatType | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        if settings is not None and (format is not None or kwargs is not None):
            raise TypeError("Provide either settings or flat format/kwargs, not both.")

        if settings is None:
            if format is None:
                raise TypeError("format is required when settings is not provided.")
            settings = DataFrameSerdeSettings(format=format, kwargs=kwargs or {})
        elif isinstance(settings, dict):
            settings = DataFrameSerdeSettings(**settings)

        super().__init__(settings=settings)

    @property
    def format(self) -> DatasetStorageFormatType:
        return self.settings.format

    @property
    def kwargs(self) -> dict[str, Any]:
        return self.settings.kwargs

    def __call__(self, value: Any, **_kwargs: Any) -> pd.DataFrame:
        """
        Deserialize a value into a pandas DataFrame.
        Args:
            value: The value to deserialize.
            **kwargs: Additional keyword arguments.
        Returns:
            A pandas DataFrame.
        """
        logger.debug(f"PandasDeserializer __call__ with format: {self.format} and args: {self.kwargs}")

        if isinstance(value, bytes):
            value = io.BytesIO(value)
        elif isinstance(value, str):
            value = io.StringIO(value)
        elif isinstance(value, (dict, list)):
            value = io.StringIO(json.dumps(value))

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
