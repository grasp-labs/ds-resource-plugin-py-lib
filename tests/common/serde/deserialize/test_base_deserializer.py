"""
**File:** ``test_base_deserializer.py``
**Region:** ``tests/common/serde/deserialize``

Description
-----------
Tests for `DataDeserializer` defaults.
"""

from typing import Any

import pytest

from ds_resource_plugin_py_lib.common.serde.deserialize.base import DataDeserializer


class ExampleDeserializer(DataDeserializer):
    """Minimal concrete DataDeserializer for testing base behaviors."""

    def __call__(self, value: Any, **kwargs: Any) -> Any:
        """Echo the provided value."""
        return value


def test_get_next_default_false():
    """get_next should return False by default."""
    deserializer = ExampleDeserializer()

    assert deserializer.get_next({}, cursor="cursor") is False


def test_get_end_cursor_default_none():
    """get_end_cursor should return None by default."""
    deserializer = ExampleDeserializer()

    assert deserializer.get_end_cursor({}) is None


def test_call_not_implemented_raises():
    """Calling base class directly should raise NotImplementedError."""
    with pytest.raises(NotImplementedError):
        DataDeserializer()(None)
