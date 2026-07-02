"""
**File:** ``test_json_default.py``
**Region:** ``tests/libs/utils``

Description
-----------
Tests for JSON serialization helpers in ``json_default``.
"""

import json
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

import numpy as np
import pandas as pd
import pytest

from ds_resource_plugin_py_lib.libs.utils.json_default import json_default


class _SampleEnum(Enum):
    ACTIVE = "active"


class _FakeScalarWithItem:
    def __init__(self, value: Any) -> None:
        self._value = value

    def item(self) -> Any:
        return self._value


class _FakeObjectWithItem:
    def item(self) -> int:
        return 42


def test_json_default_datetime():
    """Serialize datetime values as ISO-8601 strings."""
    value = datetime(2024, 3, 15, 10, 30, 0)

    assert json_default(value) == "2024-03-15T10:30:00"


def test_json_default_date():
    """Serialize date values as ISO-8601 strings."""
    value = date(2024, 3, 15)

    assert json_default(value) == "2024-03-15"


def test_json_default_decimal_uuid_enum_and_set():
    """Serialize other common non-JSON-native types."""
    assert json_default(Decimal("12.50")) == "12.50"
    assert json_default(UUID("12345678-1234-5678-1234-567812345678")) == "12345678-1234-5678-1234-567812345678"
    assert json_default(_SampleEnum.ACTIVE) == "active"
    assert json_default({1, 2}) == [1, 2]


def test_json_dumps_with_default_embeds_datetime():
    """json.dumps(..., default=json_default) should encode nested datetime values."""
    payload = {"created_at": datetime(2024, 3, 15, 10, 30, 0)}

    result = json.dumps(payload, default=json_default)

    assert json.loads(result) == {"created_at": "2024-03-15T10:30:00"}


def test_json_dumps_none_as_null():
    """None is serialized by stdlib json.dumps and does not use json_default."""
    result = json.dumps({"present": None, "when": datetime(2024, 3, 15)}, default=json_default)

    assert json.loads(result) == {"present": None, "when": "2024-03-15T00:00:00"}


def test_json_default_bytes_raises_type_error():
    """Bytes must not be silently decoded to text during JSON encoding."""
    with pytest.raises(TypeError, match="not JSON serializable"):
        json_default(b"hello")

    with pytest.raises(TypeError, match="not JSON serializable"):
        json_default(bytearray(b"hello"))


def test_json_default_unknown_type_raises_type_error():
    """Unknown types should raise TypeError like stdlib json.dumps."""
    with pytest.raises(TypeError, match="not JSON serializable"):
        json_default(object())


def test_json_default_time():
    """Serialize time values as ISO-8601 strings."""
    value = time(10, 30, 0)

    assert json_default(value) == "10:30:00"


def test_json_default_numpy_scalars():
    """Numpy scalar types should serialize via the .item() branch."""
    assert json.dumps(np.int64(42), default=json_default) == "42"
    assert json.dumps(np.float64(3.5), default=json_default) == "3.5"
    assert json.dumps(np.bool_(True), default=json_default) == "true"


def test_json_default_numpy_datetime64():
    """Numpy datetime64 values should serialize as ISO-8601 strings."""
    value = np.datetime64("2024-03-15T10:30")

    result = json.dumps(value, default=json_default)

    assert json.loads(result) == "2024-03-15T10:30:00"


def test_json_default_pandas_timestamp():
    """Pandas Timestamp values should serialize as ISO-8601 strings."""
    value = pd.Timestamp("2024-03-15 10:30:00")

    result = json.dumps(value, default=json_default)

    assert json.loads(result) == "2024-03-15T10:30:00"


def test_json_default_uses_item_for_objects_with_callable_item():
    """Objects with a callable .item() should unwrap to JSON-native values."""
    assert json.dumps(_FakeScalarWithItem(7), default=json_default) == "7"
    assert json.dumps(_FakeObjectWithItem(), default=json_default) == "42"


def test_json_dumps_nested_dict_with_mixed_leaves():
    """Deeply nested dicts should round-trip with converted leaf values."""
    payload = {
        "meta": {
            "tags": {1, 2},
            "when": datetime(2024, 3, 15, 10, 30, 0),
            "amount": Decimal("12.50"),
            "status": _SampleEnum.ACTIVE,
        }
    }

    result = json.loads(json.dumps(payload, default=json_default))

    assert result == {
        "meta": {
            "tags": [1, 2],
            "when": "2024-03-15T10:30:00",
            "amount": "12.50",
            "status": "active",
        }
    }


def test_json_dumps_list_of_dicts_with_nested_dict():
    """List input with nested dict values should preserve structure."""
    payload = [
        {
            "id": 1,
            "payload": {"nested": True, "created_at": datetime(2024, 3, 15, 10, 30, 0)},
            "tags": {"a", "b"},
        },
        {"id": 2, "payload": {"nested": False}},
    ]

    result = json.loads(json.dumps(payload, default=json_default))

    assert result[0]["id"] == 1
    assert result[0]["payload"] == {"nested": True, "created_at": "2024-03-15T10:30:00"}
    assert sorted(result[0]["tags"]) == ["a", "b"]
    assert result[1] == {"id": 2, "payload": {"nested": False}}


def test_json_dumps_default_only_called_for_non_native_leaves():
    """json.dumps should not invoke default for dict/list containers."""
    calls: list[str] = []

    def tracking_default(value: Any) -> Any:
        calls.append(type(value).__name__)
        return json_default(value)

    payload = {"meta": {"when": datetime(2024, 3, 15, 10, 30, 0)}}
    json.dumps(payload, default=tracking_default)

    assert calls == ["datetime"]
