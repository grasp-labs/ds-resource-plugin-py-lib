from typing import Any

import awswrangler as wr
import pandas as pd

from ....common.resource.dataset.storage_format import DatasetStorageFormatType
from ...serde.serialize.base import DataSerializer


class AwsWranglerSerializer(DataSerializer):
    def __init__(self, *, format: DatasetStorageFormatType, **kwargs: Any) -> None:
        self.format = format
        self.args = kwargs

    def __call__(self, obj: pd.DataFrame, **kwargs: Any) -> Any:
        boto3_session = kwargs.get("boto3_session")

        if not boto3_session:
            raise ValueError("AWS boto3 Session is required.")

        if self.format == DatasetStorageFormatType.CSV:
            return wr.s3.to_csv(
                obj,
                boto3_session=boto3_session,
                **self.args,
            )
        elif self.format == DatasetStorageFormatType.PARQUET:
            return wr.s3.to_parquet(
                obj,
                boto3_session=boto3_session,
                **self.args,
            )
        elif self.format == DatasetStorageFormatType.JSON:
            return wr.s3.to_json(
                obj,
                boto3_session=boto3_session,
                **self.args,
            )
        elif self.format == DatasetStorageFormatType.EXCEL:
            return wr.s3.to_excel(
                obj,
                boto3_session=boto3_session,
                **self.args,
            )
        elif self.format == DatasetStorageFormatType.XML:
            return wr.s3.upload(
                obj.to_xml(),
                boto3_session=boto3_session,
                **self.args,
            )
        else:
            raise ValueError(f"Unsupported format: {self.format}")
