"""
**File:** ``test_dataset_dtype_normalization.py``
**Region:** ``tests/common/resource/dataset``

Description
-----------
Cover ``dataset.dtype.normalize_dtype``/``normalize_row_schema`` against the
real PyArrow-backend strings ``pandas.DataFrame.convert_dtypes(dtype_backend="pyarrow")``
produces (empirically verified), plus already-portable input.
"""

import pandas as pd
import pyarrow as pa
import pytest

from ds_resource_plugin_py_lib.common.resource.dataset.dtype import normalize_dtype, normalize_row_schema


class TestNormalizeDtypeAgainstRealPandasOutput:
    """Each case's `raw` value is the literal string
    `str(df.convert_dtypes(dtype_backend="pyarrow").dtypes[col])` produces
    for a column of that logical type -- not a guess."""

    def test_int64(self):
        s = pd.Series([1, 2, 3]).convert_dtypes(dtype_backend="pyarrow")
        assert str(s.dtype) == "int64[pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "int64"

    def test_uint8(self):
        s = pd.array([1, 2, 3], dtype="uint8")
        converted = pd.Series(s).convert_dtypes(dtype_backend="pyarrow")
        assert str(converted.dtype) == "uint8[pyarrow]"
        assert normalize_dtype(str(converted.dtype)) == "uint8"

    def test_float64_normalizes_from_double(self):
        s = pd.Series([1.1, 2.2, 3.3]).convert_dtypes(dtype_backend="pyarrow")
        assert str(s.dtype) == "double[pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "float64"

    def test_bool(self):
        s = pd.Series([True, False]).convert_dtypes(dtype_backend="pyarrow")
        assert str(s.dtype) == "bool[pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "bool"

    def test_string(self):
        s = pd.Series(["a", "b"]).convert_dtypes(dtype_backend="pyarrow")
        assert str(s.dtype) == "string[pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "string"

    def test_large_string_normalizes_to_string(self):
        s = pd.Series(["a", "b"], dtype=pd.ArrowDtype(pa.large_string()))
        assert str(s.dtype) == "large_string[pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "string"

    def test_timestamp_drops_unit(self):
        s = pd.to_datetime(["2020-01-01", "2020-01-02"]).to_series(index=range(2))
        s = s.convert_dtypes(dtype_backend="pyarrow")
        assert str(s.dtype) == "timestamp[ns][pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "timestamp"

    def test_timestamp_with_timezone_drops_unit_and_tz(self):
        s = pd.Series([1, 2], dtype=pd.ArrowDtype(pa.timestamp("us", tz="UTC")))
        assert str(s.dtype) == "timestamp[us, tz=UTC][pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "timestamp"

    def test_date32_normalizes_to_date(self):
        s = pd.Series([1, 2, 3], dtype=pd.ArrowDtype(pa.date32()))
        assert str(s.dtype) == "date32[day][pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "date"

    def test_decimal128_normalizes_to_decimal_and_drops_precision_scale(self):
        s = pd.Series([1, 2, 3], dtype=pd.ArrowDtype(pa.decimal128(10, 2)))
        assert str(s.dtype) == "decimal128(10, 2)[pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "decimal"

    def test_list_type_keeps_base_name(self):
        s = pd.Series([[1, 2], [3]], dtype=pd.ArrowDtype(pa.list_(pa.int64())))
        assert str(s.dtype) == "list<item: int64>[pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "list"

    def test_struct_type_keeps_base_name(self):
        s = pd.Series([{"a": 1}], dtype=pd.ArrowDtype(pa.struct([("a", pa.int64())])))
        assert str(s.dtype) == "struct<a: int64>[pyarrow]"
        assert normalize_dtype(str(s.dtype)) == "struct"


class TestNormalizeDtypePortableInputPassesThrough:
    @pytest.mark.parametrize(
        ("declared", "expected"),
        [
            ("int64", "int64"),
            ("string", "string"),
            ("bool", "bool"),
            ("timestamp", "timestamp"),
            ("date", "date"),
            ("decimal", "decimal"),
            ("float64", "float64"),
        ],
    )
    def test_already_portable_names_pass_through(self, declared, expected):
        assert normalize_dtype(declared) == expected

    def test_case_insensitive(self):
        assert normalize_dtype("Int64") == "int64"
        assert normalize_dtype("STRING") == "string"

    def test_legacy_pyarrow_suffixed_declaration_still_normalizes(self):
        """Backward compatible: schemas written before normalization existed
        (using pandas-specific "[pyarrow]"-suffixed strings) still work."""
        assert normalize_dtype("int64[pyarrow]") == "int64"
        assert normalize_dtype("string[pyarrow]") == "string"

    def test_unrecognized_base_name_passes_through_lowercased(self):
        """Forward compatible: not an enforced enum -- unknown/future types
        are still comparable, just not remapped to a friendlier name."""
        assert normalize_dtype("SomeFutureType") == "somefuturetype"


class TestNormalizeRowSchema:
    def test_normalizes_every_column(self):
        raw = {"id": "int64[pyarrow]", "name": "large_string[pyarrow]", "created_at": "timestamp[ns][pyarrow]"}
        assert normalize_row_schema(raw) == {"id": "int64", "name": "string", "created_at": "timestamp"}

    def test_empty_row_schema(self):
        assert normalize_row_schema({}) == {}
