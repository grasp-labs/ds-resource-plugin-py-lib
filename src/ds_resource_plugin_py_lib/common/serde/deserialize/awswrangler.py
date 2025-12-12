import json
from io import BytesIO
from typing import Any, cast

import awswrangler as wr
import pandas as pd

from ....common.resource.dataset.storage_format import DatasetStorageFormatType
from ...serde.deserialize.base import DataDeserializer


class AwsWranglerDeserializer(DataDeserializer):
    def __init__(
        self,
        *,
        format: DatasetStorageFormatType,
        **kwargs: Any,
    ) -> None:
        self.log.info(f"AwsWranglerDeserializer initialized with format: {format} and args: {kwargs}")
        self.format = format
        self.args = kwargs

    def __call__(self, value: Any, **kwargs: Any) -> pd.DataFrame:
        boto3_session = kwargs.get("boto3_session")

        if not boto3_session:
            raise ValueError("AWS boto3 Session is required.")

        if self.format == DatasetStorageFormatType.CSV:
            return cast(
                "pd.DataFrame",
                wr.s3.read_csv(
                    path=value,
                    boto3_session=boto3_session,
                    **self.args,
                ),
            )
        elif self.format == DatasetStorageFormatType.PARQUET:
            return cast(
                "pd.DataFrame",
                wr.s3.read_parquet(
                    path=value,
                    boto3_session=boto3_session,
                    **self.args,
                ),
            )
        elif self.format == DatasetStorageFormatType.JSON:
            return cast(
                "pd.DataFrame",
                wr.s3.read_json(
                    path=value,
                    boto3_session=boto3_session,
                    **self.args,
                ),
            )
        elif self.format == DatasetStorageFormatType.SEMI_STRUCTURED_JSON:
            with BytesIO() as buffer:
                wr.s3.download(
                    path=value,
                    boto3_session=boto3_session,
                    local_file=buffer,
                )
                json_data = json.loads(buffer.getvalue().decode())
                return pd.json_normalize(json_data, **self.args)
        elif self.format == DatasetStorageFormatType.EXCEL:
            return wr.s3.read_excel(
                path=value,
                boto3_session=boto3_session,
                **self.args,
            )
        elif self.format == DatasetStorageFormatType.XML:
            with BytesIO() as buffer:
                wr.s3.download(
                    path=value,
                    boto3_session=boto3_session,
                    local_file=buffer,
                )
                return pd.read_xml(buffer, **self.args)
        else:
            raise ValueError(f"Unsupported format: {self.format}")
