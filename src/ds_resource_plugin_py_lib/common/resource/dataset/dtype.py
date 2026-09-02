"""
**File:** ``dtype.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/dataset``

Description
-----------
Normalizes PyArrow-backend pandas dtype strings to a small, portable,
engine-agnostic logical type vocabulary.

``TabularDataset.row_schema`` is meant to be a table/row data contract --
not to be confused with a JSON Schema, and not a place to leak
``convert_dtypes(dtype_backend="pyarrow")``'s implementation details.
Callers declare plain logical type names (``"int64"``, ``"string"``,
``"timestamp"``, ...); this module maps both the declared row schema and
the PyArrow-backend dtype strings pandas actually produces down to the
same vocabulary before they are compared.
"""

import re

_PYARROW_SUFFIX = "[pyarrow]"

_SPLIT_PATTERN = re.compile(r"[\[({<]")

_BASE_TYPE_ALIASES: dict[str, str] = {
    "double": "float64",
    "float": "float32",
    "halffloat": "float16",
    "large_string": "string",
    "string_view": "string",
    "large_binary": "binary",
    "binary_view": "binary",
    "date32": "date",
    "date64": "date",
    "time32": "time",
    "time64": "time",
    "decimal128": "decimal",
    "decimal256": "decimal",
}
"""
Maps PyArrow base type names that have a more portable/common equivalent to
that equivalent. Types not listed here (``int64``, ``bool``, ``string``,
``timestamp``, ``list``, ``struct``, etc.) already are the portable name and
pass through unchanged.
"""


def normalize_dtype(dtype: str) -> str:
    """
    Normalize a dtype string to a portable, engine-agnostic logical type name.

    Strips the ``[pyarrow]`` suffix ``convert_dtypes(dtype_backend="pyarrow")``
    adds, drops parameterization (timestamp unit/timezone, decimal
    precision/scale, date/time unit, nested-type element specs), and maps
    known PyArrow base type names to a small common vocabulary. Names that
    are already portable (e.g. ``"int64"``, ``"string"``) pass through
    unchanged (case-insensitively), so declared row schemas and legacy
    PyArrow-suffixed schemas both normalize to the same value.

    This is a normalization, not an enforced enum -- unrecognized base names
    pass through as their lowercased selves rather than raising, so nested
    or future PyArrow types remain comparable without needing an alias
    table update for every possible type.

    Examples:
        >>> normalize_dtype("int64[pyarrow]")
        'int64'
        >>> normalize_dtype("double[pyarrow]")
        'float64'
        >>> normalize_dtype("large_string[pyarrow]")
        'string'
        >>> normalize_dtype("timestamp[us, tz=UTC][pyarrow]")
        'timestamp'
        >>> normalize_dtype("date32[day][pyarrow]")
        'date'
        >>> normalize_dtype("decimal128(10, 2)[pyarrow]")
        'decimal'
        >>> normalize_dtype("int64")
        'int64'
        >>> normalize_dtype("STRING")
        'string'

    Args:
        dtype: A dtype string -- either a plain portable logical type name
            or a PyArrow-backend pandas dtype string.

    Returns:
        The normalized, portable logical type name.
    """
    raw = dtype.strip()
    if raw.endswith(_PYARROW_SUFFIX):
        raw = raw[: -len(_PYARROW_SUFFIX)]

    base = _SPLIT_PATTERN.split(raw, maxsplit=1)[0].strip().lower()
    return _BASE_TYPE_ALIASES.get(base, base)


def normalize_row_schema(row_schema: dict[str, str]) -> dict[str, str]:
    """
    Normalize every dtype value in a column-name -> dtype-string mapping.

    Args:
        row_schema: A mapping of column name to dtype string.

    Returns:
        The same column names mapped to their normalized dtype strings.
    """
    return {column: normalize_dtype(dtype) for column, dtype in row_schema.items()}
