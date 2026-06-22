"""
**File:** ``binary.py``
**Region:** ``ds_resource_plugin_py_lib/common/serde``

Description
-----------
Helpers for serializing and deserializing binary payloads via DataFrames.
"""

import io
from typing import Any

import pandas as pd
from ds_common_serde_py_lib.errors import DeserializationError, SerializationError

_BINARY_KWARGS = frozenset({"column", "row", "encoding"})
_DEFAULT_COLUMN = "binary"
_DEFAULT_ROW = 0


def binary_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Return kwargs with binary-specific keys removed."""
    return {key: value for key, value in kwargs.items() if key not in _BINARY_KWARGS}


def deserialize_binary(
    value: Any,
    *,
    column: str = _DEFAULT_COLUMN,
    encoding: str | None = None,
) -> pd.DataFrame:
    """
    Wrap raw binary input in a single-row DataFrame.

    Args:
        value: Binary payload as ``bytes``, ``bytearray``, ``BytesIO``, or ``str``.
        column: Column name for the binary value.
        encoding: When set, encode ``str`` input with this encoding.

    Returns:
        A one-row DataFrame containing the binary payload.

    Raises:
        DeserializationError: If the input is not binary.
    """
    if isinstance(value, io.BytesIO):
        data = value.getvalue()
    elif isinstance(value, bytes):
        data = value
    elif isinstance(value, bytearray):
        data = bytes(value)
    elif isinstance(value, str):
        if encoding is None:
            raise DeserializationError(
                message="Expected binary input, got str. Provide encoding to convert text.",
                details={"column": column, "type": type(value).__name__},
            )
        try:
            data = value.encode(encoding)
        except (UnicodeEncodeError, LookupError) as exc:
            raise DeserializationError(
                message=f"Failed to encode text input with {encoding!r}: {exc}",
                details={"column": column, "encoding": encoding, "error": str(exc)},
            ) from exc
    else:
        raise DeserializationError(
            message=f"Expected binary input, got {type(value)}",
            details={"column": column, "type": type(value).__name__},
        )

    return pd.DataFrame({column: [data]})


def serialize_binary(
    obj: pd.DataFrame,
    *,
    column: str = _DEFAULT_COLUMN,
    row: int = _DEFAULT_ROW,
    encoding: str | None = None,
) -> bytes:
    """
    Extract binary payload from a DataFrame row and column.

    Args:
        obj: Source DataFrame.
        column: Column containing the binary value.
        row: Row index to read from.
        encoding: When set, encode ``str`` cell values with this encoding.

    Returns:
        The binary payload as ``bytes``.

    Raises:
        SerializationError: If the column, row, or cell value is invalid.
    """
    if column not in obj.columns:
        raise SerializationError(
            message=f"Column '{column}' not found in DataFrame",
            details={"column": column, "columns": list(obj.columns)},
        )
    if row < 0 or row >= len(obj):
        raise SerializationError(
            message=f"Row {row} is out of bounds for DataFrame with {len(obj)} rows",
            details={"column": column, "row": row, "row_count": len(obj)},
        )

    value = obj.iloc[row][column]
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, str):
        if encoding is None:
            raise SerializationError(
                message=(f"Expected bytes in column '{column}', got str. Provide encoding to convert text."),
                details={"column": column, "row": row, "type": type(value).__name__},
            )
        try:
            return value.encode(encoding)
        except (UnicodeEncodeError, LookupError) as exc:
            raise SerializationError(
                message=f"Failed to encode text in column '{column}' with {encoding!r}: {exc}",
                details={"column": column, "row": row, "encoding": encoding, "error": str(exc)},
            ) from exc

    raise SerializationError(
        message=f"Expected bytes in column '{column}', got {type(value)}",
        details={"column": column, "row": row, "type": type(value).__name__},
    )
