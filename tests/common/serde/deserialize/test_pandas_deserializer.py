"""
**File:** ``test_pandas_deserializer.py``
**Region:** ``tests/common/serde/deserialize``

Description
-----------
Tests for `PandasDeserializer` covering formats and edge cases.
"""

import io
import json
from typing import cast
from unittest.mock import patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from ds_resource_plugin_py_lib.common.resource.dataset.storage_format import DatasetStorageFormatType
from ds_resource_plugin_py_lib.common.serde.deserialize.pandas import PandasDeserializer


class TestPandasDeserializer:
    """Validate PandasDeserializer behaviors across supported formats."""

    def test_csv_bytes_to_dataframe(self, sample_dataframe):
        """Ensure CSV bytes are parsed into a DataFrame."""
        csv_bytes = sample_dataframe.to_csv(index=False).encode("utf-8")
        deserializer = PandasDeserializer(format=DatasetStorageFormatType.CSV)

        result = deserializer(csv_bytes)

        assert_frame_equal(result, sample_dataframe)

    def test_json_string_to_dataframe(self, sample_dataframe):
        """Ensure JSON string input is handled correctly."""
        json_string = sample_dataframe.to_json(orient="records")
        deserializer = PandasDeserializer(format=DatasetStorageFormatType.JSON)

        result = deserializer(json_string)

        expected = pd.read_json(io.StringIO(json_string))
        assert_frame_equal(result.reset_index(drop=True), expected)

    def test_semi_structured_json_normalization(self, semi_structured_json):
        """Normalize semi-structured JSON input."""
        deserializer = PandasDeserializer(format=DatasetStorageFormatType.SEMI_STRUCTURED_JSON)

        result = deserializer(semi_structured_json)

        expected = pd.json_normalize(semi_structured_json)
        assert_frame_equal(result, expected)

    def test_unsupported_format_raises(self):
        """Raise ValueError when format is unsupported."""
        bad_format = cast("DatasetStorageFormatType", "OTHER")
        deserializer = PandasDeserializer(format=bad_format)

        with pytest.raises(ValueError):
            deserializer("value")

    def test_semi_structured_handles_bytes_io(self, semi_structured_json):
        """Ensure BytesIO input is decoded before normalization."""
        json_bytes = json.dumps(semi_structured_json).encode("utf-8")
        deserializer = PandasDeserializer(format=DatasetStorageFormatType.SEMI_STRUCTURED_JSON)

        result = deserializer(json_bytes)

        expected = pd.json_normalize(semi_structured_json)
        assert_frame_equal(result, expected)

    def test_semi_structured_handles_stringio(self, semi_structured_json):
        """Ensure StringIO input is parsed to JSON before normalization."""
        json_text = json.dumps(semi_structured_json)
        deserializer = PandasDeserializer(format=DatasetStorageFormatType.SEMI_STRUCTURED_JSON)

        result = deserializer(json_text)

        expected = pd.json_normalize(semi_structured_json)
        assert_frame_equal(result, expected)

    def test_parquet_reader_invoked(self, sample_dataframe):
        """Parquet format should delegate to pandas.read_parquet."""
        deserializer = PandasDeserializer(format=DatasetStorageFormatType.PARQUET)
        with patch(
            "ds_resource_plugin_py_lib.common.serde.deserialize.pandas.pd.read_parquet", return_value=sample_dataframe
        ) as reader:
            result = deserializer(sample_dataframe)
        assert_frame_equal(result, sample_dataframe)
        reader.assert_called_once()

    def test_semi_structured_stringio(self, semi_structured_json):
        """Ensure StringIO input is parsed and normalized."""
        json_text = json.dumps(semi_structured_json)
        deserializer = PandasDeserializer(format=DatasetStorageFormatType.SEMI_STRUCTURED_JSON)

        result = deserializer(io.StringIO(json_text))

        expected = pd.json_normalize(semi_structured_json)
        assert_frame_equal(result, expected)

    def test_semi_structured_plain_string(self, semi_structured_json):
        """Ensure raw JSON string input is normalized."""
        json_text = json.dumps(semi_structured_json)
        deserializer = PandasDeserializer(format=DatasetStorageFormatType.SEMI_STRUCTURED_JSON)

        result = deserializer(json_text)

        expected = pd.json_normalize(semi_structured_json)
        assert_frame_equal(result, expected)

    def test_semi_structured_bytesio(self, semi_structured_json):
        """Ensure BytesIO input is decoded and normalized."""
        json_bytes = json.dumps(semi_structured_json).encode("utf-8")
        buffer = io.BytesIO(json_bytes)
        deserializer = PandasDeserializer(format=DatasetStorageFormatType.SEMI_STRUCTURED_JSON)

        result = deserializer(buffer)

        expected = pd.json_normalize(semi_structured_json)
        assert_frame_equal(result, expected)

    def test_semi_structured_list_input_hits_str_branch(self, semi_structured_json):
        """List input is json-dumped then normalized (covers str branch)."""
        deserializer = PandasDeserializer(format=DatasetStorageFormatType.SEMI_STRUCTURED_JSON)

        result = deserializer(semi_structured_json)

        expected = pd.json_normalize(semi_structured_json)
        assert_frame_equal(result, expected)
