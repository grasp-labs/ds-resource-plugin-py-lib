"""
**File:** ``awswrangler.py``
**Region:** ``ds_resource_plugin_py_lib/common/serde/serialize``

Description
-----------
Serialize a pandas DataFrame into a value using awswrangler.

Example
-------
.. code-block:: python

    from ds_resource_plugin_py_lib.common.serde.serialize.awswrangler import AwsWranglerSerializer
    from ds_resource_plugin_py_lib.common.resource.dataset.storage_format import DatasetStorageFormatType

    serializer = AwsWranglerSerializer(format=DatasetStorageFormatType.CSV)
    result = serializer(df, boto3_session=boto3_session)
"""

from dataclasses import dataclass, field
from typing import Any

import awswrangler as wr
import pandas as pd

from ....common.resource.dataset.storage_format import DatasetStorageFormatType
from ...serde.serialize.base import DataSerializer


@dataclass(kw_only=True)
class AwsWranglerSerializer(DataSerializer):
    format: DatasetStorageFormatType
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __call__(self, obj: pd.DataFrame, **kwargs: Any) -> Any:
        """
        Serialize a pandas DataFrame into a value.
        Args:
            obj: The pandas DataFrame to serialize.
            **kwargs: Additional keyword arguments.
        Returns:
            A value.
        """
        self.log.info(f"AwsWranglerSerializer __call__ with format: {self.format} and args: {self.kwargs}")
        boto3_session = kwargs.get("boto3_session")
        if not boto3_session:
            raise ValueError("AWS boto3 Session is required.")

        if self.format == DatasetStorageFormatType.CSV:
            return wr.s3.to_csv(
                obj,
                boto3_session=boto3_session,
                **self.kwargs,
            )
        elif self.format == DatasetStorageFormatType.PARQUET:
            return wr.s3.to_parquet(
                obj,
                boto3_session=boto3_session,
                **self.kwargs,
            )
        elif self.format == DatasetStorageFormatType.JSON:
            return wr.s3.to_json(
                obj,
                boto3_session=boto3_session,
                **self.kwargs,
            )
        elif self.format == DatasetStorageFormatType.EXCEL:
            return wr.s3.to_excel(
                obj,
                boto3_session=boto3_session,
                **self.kwargs,
            )
        elif self.format == DatasetStorageFormatType.XML:
            return wr.s3.upload(
                obj.to_xml(),
                boto3_session=boto3_session,
                **self.kwargs,
            )
        else:
            raise ValueError(f"Unsupported format: {self.format}")
