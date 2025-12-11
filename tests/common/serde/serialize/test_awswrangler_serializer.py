"""
File: test_awswrangler_serializer.py
Description: Tests for AwsWranglerSerializer covering supported formats and validation.
Region: packages/shared
"""

from typing import cast
from unittest.mock import patch

import pytest

from ds_resource_plugin_py_lib.common.resource.dataset.storage_format import DatasetStorageFormatType
from ds_resource_plugin_py_lib.common.serde.serialize.awswrangler import AwsWranglerSerializer


class TestAwsWranglerSerializer:
    """Validate AwsWranglerSerializer across supported formats."""

    @pytest.mark.parametrize(
        ("format_type", "method_name"),
        [
            (DatasetStorageFormatType.CSV, "to_csv"),
            (DatasetStorageFormatType.PARQUET, "to_parquet"),
            (DatasetStorageFormatType.JSON, "to_json"),
            (DatasetStorageFormatType.EXCEL, "to_excel"),
        ],
    )
    def test_tabular_formats(self, format_type, method_name, sample_dataframe, boto3_session):
        """Ensure DataFrame is written using awswrangler.s3 helpers."""
        target = f"ds_resource_plugin_py_lib.common.serde.serialize.awswrangler.wr.s3.{method_name}"
        with patch(target, return_value="ok") as mock_writer:
            serializer = AwsWranglerSerializer(format=format_type)

            result = serializer(sample_dataframe, boto3_session=boto3_session)

            assert result == "ok"
            mock_writer.assert_called_once_with(sample_dataframe, boto3_session=boto3_session)

    def test_xml_uploads_string(self, sample_dataframe, boto3_session):
        """Convert DataFrame to XML and upload via awswrangler.s3.upload."""
        target = "ds_resource_plugin_py_lib.common.serde.serialize.awswrangler.wr.s3.upload"
        with patch(target, return_value="uploaded") as mock_upload:
            serializer = AwsWranglerSerializer(format=DatasetStorageFormatType.XML, path="s3://bucket/data.xml")

            result = serializer(sample_dataframe, boto3_session=boto3_session)

            assert result == "uploaded"
            mock_upload.assert_called_once()

    def test_missing_boto3_session_raises(self, sample_dataframe):
        """Require boto3_session for all writes."""
        serializer = AwsWranglerSerializer(format=DatasetStorageFormatType.CSV)

        with pytest.raises(ValueError, match=r"AWS boto3 Session is required\."):
            serializer(sample_dataframe)

    def test_unsupported_format_raises(self, sample_dataframe, boto3_session):
        """Raise ValueError for unsupported formats."""
        serializer = AwsWranglerSerializer(format=cast("DatasetStorageFormatType", "OTHER"))

        with pytest.raises(ValueError):
            serializer(sample_dataframe, boto3_session=boto3_session)
