from typing import Any

import pandas as pd

from ...resource.dataset.storage_format import DatasetStorageFormatType
from .base import DataSerializer


class PandasSerializer(DataSerializer):
    def __init__(
        self,
        *,
        format: DatasetStorageFormatType,
        **kwargs: Any,
    ) -> None:
        self.format = format
        self.args = kwargs or {}

    def __call__(self, obj: Any, **_kwargs: Any) -> Any:
        if not isinstance(obj, pd.DataFrame):
            raise TypeError(f"Expected pd.DataFrame, got {type(obj)}")
        value = obj
        default_float_format = "%.2f"

        def _ensure_float_format() -> None:
            if "float_format" not in self.args:
                self.args["float_format"] = default_float_format

        if self.format == DatasetStorageFormatType.CSV:
            _ensure_float_format()
            return value.to_csv(**self.args)
        elif self.format == DatasetStorageFormatType.PARQUET:
            return value.to_parquet(**self.args)
        elif self.format in (
            DatasetStorageFormatType.JSON,
            DatasetStorageFormatType.SEMI_STRUCTURED_JSON,
        ):
            return value.to_json(**self.args)
        elif self.format == DatasetStorageFormatType.EXCEL:
            _ensure_float_format()
            return value.to_excel(**self.args)
        elif self.format == DatasetStorageFormatType.XML:
            return value.to_xml(**self.args)
        else:
            raise ValueError(f"Unsupported format: {self.format}")
