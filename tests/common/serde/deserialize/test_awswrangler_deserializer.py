"""
File: test_awswrangler_deserializer.py
Description: Tests for AwsWranglerDeserializer covering supported formats and validation.
Region: packages/shared
"""

import json
from typing import cast
from unittest.mock import ANY, patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from ds_resource_plugin_py_lib.common.resource.dataset.storage_format import DatasetStorageFormatType
from ds_resource_plugin_py_lib.common.serde.deserialize.awswrangler import AwsWranglerDeserializer


class TestAwsWranglerDeserializer:
    """Validate AwsWranglerDeserializer for all supported formats."""

    @pytest.mark.parametrize(
        ("format_type", "method_name"),
        [
            (DatasetStorageFormatType.CSV, "read_csv"),
            (DatasetStorageFormatType.PARQUET, "read_parquet"),
            (DatasetStorageFormatType.JSON, "read_json"),
        ],
    )
    def test_tabular_formats(self, format_type, method_name, sample_dataframe, boto3_session):
        """Ensure tabular formats delegate to awswrangler.s3 readers."""
        path = "s3://bucket/key"
        target = f"ds_resource_plugin_py_lib.common.serde.deserialize.awswrangler.wr.s3.{method_name}"
        with patch(target, return_value=sample_dataframe) as mock_reader:
            deserializer = AwsWranglerDeserializer(format=format_type)

            result = deserializer(path, boto3_session=boto3_session)

            assert_frame_equal(result, sample_dataframe)
            mock_reader.assert_called_once_with(path=path, boto3_session=boto3_session)

    def test_semi_structured_json(self, semi_structured_json, boto3_session):
        """Download semi-structured JSON and normalize it."""
        path = "s3://bucket/structured.json"
        json_bytes = json.dumps(semi_structured_json).encode("utf-8")

        def fake_download(path, boto3_session, local_file):
            local_file.write(json_bytes)
            local_file.seek(0)

        with patch(
            "ds_resource_plugin_py_lib.common.serde.deserialize.awswrangler.wr.s3.download", side_effect=fake_download
        ) as mock_download:
            deserializer = AwsWranglerDeserializer(format=DatasetStorageFormatType.SEMI_STRUCTURED_JSON)

            result = deserializer(path, boto3_session=boto3_session)

            expected = pd.json_normalize(semi_structured_json)
            assert_frame_equal(result, expected)
            mock_download.assert_called_once_with(path=path, boto3_session=boto3_session, local_file=ANY)

    def test_excel_format(self, sample_dataframe, boto3_session):
        """Delegate EXCEL to awswrangler.s3.read_excel."""
        path = "s3://bucket/workbook.xlsx"
        with patch(
            "ds_resource_plugin_py_lib.common.serde.deserialize.awswrangler.wr.s3.read_excel", return_value=sample_dataframe
        ) as mock_read:
            deserializer = AwsWranglerDeserializer(format=DatasetStorageFormatType.EXCEL)

            result = deserializer(path, boto3_session=boto3_session)

            assert_frame_equal(result, sample_dataframe)
            mock_read.assert_called_once_with(path=path, boto3_session=boto3_session)

    def test_xml_format(self, sample_dataframe, boto3_session):
        """Download XML and parse through pandas.read_xml."""
        path = "s3://bucket/data.xml"
        xml_payload = b"<root><row><id>1</id></row></root>"

        def fake_download(path, boto3_session, local_file):
            local_file.write(xml_payload)
            local_file.seek(0)

        with (
            patch(
                "ds_resource_plugin_py_lib.common.serde.deserialize.awswrangler.wr.s3.download", side_effect=fake_download
            ) as mock_download,
            patch(
                "ds_resource_plugin_py_lib.common.serde.deserialize.awswrangler.pd.read_xml", return_value=sample_dataframe
            ) as mock_read_xml,
        ):
            deserializer = AwsWranglerDeserializer(format=DatasetStorageFormatType.XML)

            result = deserializer(path, boto3_session=boto3_session)

            assert_frame_equal(result, sample_dataframe)
            mock_download.assert_called_once_with(path=path, boto3_session=boto3_session, local_file=ANY)
            mock_read_xml.assert_called_once()

    def test_missing_boto3_session_raises(self):
        """Require boto3_session for all reads."""
        deserializer = AwsWranglerDeserializer(format=DatasetStorageFormatType.CSV)

        with pytest.raises(ValueError, match=r"AWS boto3 Session is required\."):
            deserializer("s3://bucket/key")

    def test_unsupported_format_raises(self, boto3_session):
        """Raise ValueError for unsupported formats."""
        bad_format = cast("DatasetStorageFormatType", "OTHER")
        deserializer = AwsWranglerDeserializer(format=bad_format)

        with pytest.raises(ValueError, match="Unsupported format"):
            deserializer("s3://bucket/key", boto3_session=boto3_session)
