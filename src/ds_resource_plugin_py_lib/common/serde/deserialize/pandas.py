import io
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

import pandas as pd

from ....common.resource.dataset.storage_format import DatasetStorageFormatType
from ...serde.deserialize.base import DataDeserializer


class PandasDeserializer(DataDeserializer):
    def __init__(
        self,
        *,
        format: DatasetStorageFormatType,
        **kwargs: Any,
    ) -> None:
        self.log.info(f"PandasDeserializer initialized with format: {format} and args: {kwargs}")
        self.format = format
        self.args = kwargs

    def __call__(self, value: Any, **_kwargs: Any) -> pd.DataFrame:
        if isinstance(value, bytes):
            value = io.BytesIO(value)
        elif isinstance(value, str):
            value = io.StringIO(value)
        elif isinstance(value, (dict, list)):
            value = json.dumps(value)

        format_readers: dict[DatasetStorageFormatType, Callable[[Any], pd.DataFrame]] = {
            DatasetStorageFormatType.CSV: lambda v: pd.read_csv(v, **self.args),
            DatasetStorageFormatType.PARQUET: lambda v: pd.read_parquet(v, **self.args),
            DatasetStorageFormatType.JSON: lambda v: pd.read_json(v, **self.args),
            DatasetStorageFormatType.EXCEL: lambda v: pd.read_excel(v, **self.args),
            DatasetStorageFormatType.XML: lambda v: pd.read_xml(v, **self.args),
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
            return pd.json_normalize(value, **self.args)

        reader = format_readers.get(self.format)
        if reader:
            return reader(value)

        raise ValueError(f"Unsupported format: {self.format}")
