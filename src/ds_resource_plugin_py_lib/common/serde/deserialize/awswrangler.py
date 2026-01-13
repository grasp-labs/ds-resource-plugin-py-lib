"""
**File:** ``awswrangler.py``
**Region:** ``ds_resource_plugin_py_lib/common/serde/deserialize``

Description
-----------
Deserialize a value into a pandas DataFrame using awswrangler.

Example
-------
.. code-block:: python

    import boto3

    from ds_resource_plugin_py_lib.common.serde.deserialize.awswrangler import AwsWranglerDeserializer
    from ds_resource_plugin_py_lib.common.resource.dataset.storage_format import DatasetStorageFormatType

    boto3_session = boto3.Session()
    deserializer = AwsWranglerDeserializer(format=DatasetStorageFormatType.PARQUET)

    df = deserializer("s3://my-bucket/path/to/data.parquet", boto3_session=boto3_session)
"""

import json
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, cast

import awswrangler as wr
import pandas as pd

from ....common.resource.dataset.storage_format import DatasetStorageFormatType
from ...serde.deserialize.base import DataDeserializer


@dataclass(kw_only=True)
class AwsWranglerDeserializer(DataDeserializer):
    format: DatasetStorageFormatType
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __call__(self, value: Any, **kwargs: Any) -> pd.DataFrame:
        """
        Deserialize a value into a pandas DataFrame.
        Args:
            value: The value to deserialize.
            **kwargs: Additional keyword arguments.
        Returns:
            A pandas DataFrame.
        """
        self.log.info(f"AwsWranglerDeserializer __call__ with format: {self.format} and args: {self.kwargs}")
        boto3_session = kwargs.get("boto3_session")
        if not boto3_session:
            raise ValueError("AWS boto3 Session is required.")

        if self.format == DatasetStorageFormatType.CSV:
            return cast(
                "pd.DataFrame",
                wr.s3.read_csv(
                    path=value,
                    boto3_session=boto3_session,
                    **self.kwargs,
                ),
            )
        elif self.format == DatasetStorageFormatType.PARQUET:
            return cast(
                "pd.DataFrame",
                wr.s3.read_parquet(
                    path=value,
                    boto3_session=boto3_session,
                    **self.kwargs,
                ),
            )
        elif self.format == DatasetStorageFormatType.JSON:
            return cast(
                "pd.DataFrame",
                wr.s3.read_json(
                    path=value,
                    boto3_session=boto3_session,
                    **self.kwargs,
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
                return pd.json_normalize(json_data, **self.kwargs)
        elif self.format == DatasetStorageFormatType.EXCEL:
            return wr.s3.read_excel(
                path=value,
                boto3_session=boto3_session,
                **self.kwargs,
            )
        elif self.format == DatasetStorageFormatType.XML:
            with BytesIO() as buffer:
                wr.s3.download(
                    path=value,
                    boto3_session=boto3_session,
                    local_file=buffer,
                )
                return pd.read_xml(buffer, **self.kwargs)
        else:
            raise ValueError(f"Unsupported format: {self.format}")
