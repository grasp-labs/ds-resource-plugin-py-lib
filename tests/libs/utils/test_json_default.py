"""
**File:** ``test_json_default.py``
**Region:** ``tests/libs/utils``

Description
-----------
Tests for JSON serialization helpers in ``json_default``.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

import pytest

from ds_resource_plugin_py_lib.libs.utils.json_default import json_default


class _SampleEnum(Enum):
    ACTIVE = "active"


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
