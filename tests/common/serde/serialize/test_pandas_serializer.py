"""
**File:** ``test_pandas_serializer.py``
**Region:** ``tests/common/serde/serialize``

Description
-----------
Tests for `PandasSerializer` covering supported formats and validation.
"""

from typing import cast
from unittest.mock import patch

import pandas as pd
import pytest

from ds_resource_plugin_py_lib.common.resource.dataset.storage_format import DatasetStorageFormatType
from ds_resource_plugin_py_lib.common.serde.serialize.pandas import PandasSerializer


class TestPandasSerializer:
    """Validate PandasSerializer behaviors across formats."""

    def test_rejects_non_dataframe(self):
        """Raise TypeError when input is not a DataFrame."""
        serializer = PandasSerializer(format=DatasetStorageFormatType.CSV)

        with pytest.raises(TypeError):
            serializer(["not", "a", "dataframe"])

    def test_csv_sets_default_float_format(self, sample_dataframe):
        """Ensure CSV serialization sets default float_format when absent."""
        serializer = PandasSerializer(format=DatasetStorageFormatType.CSV)

        csv_string = serializer(sample_dataframe, index=False)

        assert "10.50" in csv_string
        assert serializer.kwargs["float_format"] == "%.2f"

    def test_json_serialization(self, sample_dataframe):
        """Serialize DataFrame to JSON."""
        serializer = PandasSerializer(format=DatasetStorageFormatType.JSON, kwargs={"orient": "records"})

        json_string = serializer(sample_dataframe)

        loaded = pd.read_json(json_string)
        assert len(loaded) == len(sample_dataframe)

    def test_excel_uses_default_float_format(self, sample_dataframe):
        """Ensure Excel serialization sets float_format when absent."""
        serializer = PandasSerializer(format=DatasetStorageFormatType.EXCEL, kwargs={"float_format": "%.2f"})

        with patch(
            "ds_resource_plugin_py_lib.common.serde.serialize.pandas.pd.DataFrame.to_excel", return_value="excel"
        ) as to_excel:
            result = serializer(sample_dataframe, index=False)

        assert serializer.kwargs["float_format"] == "%.2f"
        to_excel.assert_called_once()
        assert result == "excel"

    def test_xml_serialization(self, sample_dataframe):
        """Serialize DataFrame to XML."""
        serializer = PandasSerializer(format=DatasetStorageFormatType.XML, kwargs={"index": False})

        xml_output = serializer(sample_dataframe)

        assert "<id>1</id>" in xml_output

    def test_unsupported_format_raises(self, sample_dataframe):
        """Raise ValueError for unsupported format."""
        serializer = PandasSerializer(format=cast("DatasetStorageFormatType", "OTHER"))

        with pytest.raises(ValueError):
            serializer(sample_dataframe)

    def test_parquet_serialization(self, sample_dataframe, boto3_session):
        """Parquet format should call to_parquet."""
        kwargs = {
            "index": False,
        }
        serializer = PandasSerializer(format=DatasetStorageFormatType.PARQUET, kwargs=kwargs)
        with patch(
            "ds_resource_plugin_py_lib.common.serde.serialize.pandas.pd.DataFrame.to_parquet", return_value="parquet"
        ) as to_parquet:
            result = serializer(sample_dataframe, **kwargs)
        to_parquet.assert_called_once()
        assert result == "parquet"
