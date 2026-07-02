"""
**File:** ``test_binary.py``
**Region:** ``tests/common/serde``

Description
-----------
Tests for binary serde helpers.
"""

import io

import pandas as pd
import pytest
from ds_common_serde_py_lib.errors import DeserializationError, SerializationError
from pandas.testing import assert_frame_equal

from ds_resource_plugin_py_lib.common.serde.binary import (
    binary_kwargs,
    deserialize_binary,
    serialize_binary,
)


class TestBinarySerde:
    """Validate shared binary serialize/deserialize helpers."""

    def test_deserialize_bytes(self):
        """Wrap raw bytes in a single-row DataFrame."""
        payload = b"hello"

        result = deserialize_binary(payload)

        assert_frame_equal(result, pd.DataFrame({"binary": [payload]}))

    def test_deserialize_bytesio(self):
        """Wrap BytesIO content in a single-row DataFrame."""
        payload = b"hello"
        buffer = io.BytesIO(payload)

        result = deserialize_binary(buffer, column="content")

        assert_frame_equal(result, pd.DataFrame({"content": [payload]}))

    def test_deserialize_rejects_str_without_encoding(self):
        """Raise DeserializationError for str input without encoding."""
        with pytest.raises(DeserializationError, match="Provide encoding"):
            deserialize_binary("not-binary")

    def test_deserialize_str_with_encoding(self):
        """Encode str input when encoding is provided."""
        result = deserialize_binary("café", encoding="utf-8")

        assert_frame_equal(result, pd.DataFrame({"binary": ["café".encode()]}))

    def test_deserialize_invalid_encoding_raises(self):
        """Raise DeserializationError when encoding fails."""
        with pytest.raises(DeserializationError, match="Failed to encode text input"):
            deserialize_binary("café", encoding="ascii")

    def test_deserialize_rejects_non_binary(self):
        """Raise DeserializationError for unsupported input types."""
        with pytest.raises(DeserializationError, match="Expected binary input"):
            deserialize_binary(123)

    def test_serialize_default_column_and_row(self):
        """Extract binary from the default column and row."""
        payload = b"payload"
        df = pd.DataFrame({"binary": [b"other", payload]})

        result = serialize_binary(df, row=1)

        assert result == payload

    def test_serialize_custom_column(self):
        """Extract binary from a custom column."""
        payload = b"payload"
        df = pd.DataFrame({"content": [payload]})

        result = serialize_binary(df, column="content")

        assert result == payload

    def test_serialize_missing_column_raises(self):
        """Raise SerializationError when the column is absent."""
        df = pd.DataFrame({"other": [b"x"]})

        with pytest.raises(SerializationError, match="Column 'binary' not found"):
            serialize_binary(df)

    def test_serialize_out_of_bounds_row_raises(self):
        """Raise SerializationError when the row index is invalid."""
        df = pd.DataFrame({"binary": [b"x"]})

        with pytest.raises(SerializationError, match="Row 3 is out of bounds"):
            serialize_binary(df, row=3)

    def test_serialize_str_without_encoding_raises(self):
        """Raise SerializationError when a str cell is provided without encoding."""
        df = pd.DataFrame({"binary": ["text"]})

        with pytest.raises(SerializationError, match="Provide encoding"):
            serialize_binary(df)

    def test_serialize_str_with_encoding(self):
        """Encode str cell values when encoding is provided."""
        df = pd.DataFrame({"binary": ["café"]})

        result = serialize_binary(df, encoding="utf-8")

        assert result == "café".encode()

    def test_serialize_invalid_encoding_raises(self):
        """Raise SerializationError when encoding fails."""
        df = pd.DataFrame({"binary": ["café"]})

        with pytest.raises(SerializationError, match="Failed to encode text"):
            serialize_binary(df, encoding="ascii")

    def test_binary_kwargs_filters_binary_specific_keys(self):
        """Remove binary-specific kwargs before passing to backends."""
        kwargs = {
            "column": "binary",
            "row": 0,
            "encoding": "utf-8",
            "path": "s3://bucket/key",
        }

        result = binary_kwargs(kwargs)

        assert result == {"path": "s3://bucket/key"}
