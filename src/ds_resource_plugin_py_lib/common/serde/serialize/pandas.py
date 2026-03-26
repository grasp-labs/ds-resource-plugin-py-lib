"""
**File:** ``pandas.py``
**Region:** ``ds_resource_plugin_py_lib/common/serde/serialize``

Description
-----------
Serialize a pandas DataFrame into a value.

Example
-------
.. code-block:: python

    import pandas as pd

    from ds_resource_plugin_py_lib.common.resource.dataset.storage_format import DatasetStorageFormatType
    from ds_resource_plugin_py_lib.common.serde.serialize.pandas import PandasSerializer

    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    serializer = PandasSerializer(format=DatasetStorageFormatType.CSV)
    csv_text = serializer(df, index=False)
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from ds_common_logger_py_lib import Logger

from ...resource.dataset.storage_format import DatasetStorageFormatType
from ..base import DataFrameSerdeSettings
from .base import DataSerializer

logger = Logger.get_logger(__name__, package=True)


@dataclass(kw_only=True)
class PandasSerializer(DataSerializer):
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

    def __call__(self, obj: Any, **_kwargs: Any) -> Any:
        """
        Serialize a pandas DataFrame into a value.
        Args:
            obj: The pandas DataFrame to serialize.
            **kwargs: Additional keyword arguments.
        Returns:
            A value.
        """
        logger.debug(f"PandasSerializer __call__ with format: {self.format} and args: {self.kwargs}")
        if not isinstance(obj, pd.DataFrame):
            raise TypeError(f"Expected pd.DataFrame, got {type(obj)}")
        value = obj
        default_float_format = "%.2f"

        def _ensure_float_format() -> None:
            if "float_format" not in self.kwargs:
                self.kwargs["float_format"] = default_float_format

        if self.format == DatasetStorageFormatType.CSV:
            _ensure_float_format()
            return value.to_csv(**self.kwargs)
        elif self.format == DatasetStorageFormatType.PARQUET:
            return value.to_parquet(**self.kwargs)
        elif self.format in (
            DatasetStorageFormatType.JSON,
            DatasetStorageFormatType.SEMI_STRUCTURED_JSON,
        ):
            return value.to_json(**self.kwargs)
        elif self.format == DatasetStorageFormatType.EXCEL:
            _ensure_float_format()
            return value.to_excel(**self.kwargs)
        elif self.format == DatasetStorageFormatType.XML:
            return value.to_xml(**self.kwargs)
        else:
            raise ValueError(f"Unsupported format: {self.format}")
