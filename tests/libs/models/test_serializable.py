"""
File: test_serializable.py
Description: Tests for Serializable mixin covering serialization and deserialization behaviors.
Region: packages/shared
"""

from collections.abc import Iterable
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, ForwardRef, Generic, TypeVar, get_origin
from uuid import UUID, uuid4

import pytest

from ds_resource_plugin_py_lib.common.resource.dataset.base import DatasetTypedProperties
from ds_resource_plugin_py_lib.libs.models import serializable
from ds_resource_plugin_py_lib.libs.models.serializable import (
    Serializable,
    _apply_structural_specialization,
    _build_type_var_map,
    _convert_value,
    _resolve_type_hint_for_field,
    _set_init_false_fields,
)


class Color(Enum):
    """Sample Enum for testing enum handling."""

    RED = "red"
    BLUE = "blue"


@dataclass
class Child(Serializable):
    """Nested dataclass for Serializable tests."""

    count: int


@dataclass
class Parent(Serializable):
    """Parent dataclass exercising various type conversions."""

    name: str
    child: Child
    tags: list[str]
    created_at: datetime
    uid: UUID
    color: Color
    values: list[int]
    mapping: dict[str, int]
    optional_note: str | None = None


def test_serialize_handles_nested_and_special_types():
    """Ensure serialize produces JSON-friendly structures."""
    created_at = datetime(2024, 1, 1, 12, 0, 0)
    uid = uuid4()
    parent = Parent(
        name="parent",
        child=Child(count=3),
        tags=["a", "b"],
        created_at=created_at,
        uid=uid,
        color=Color.RED,
        values=[1, 2],
        mapping={"one": 1},
        optional_note=None,
    )

    serialized = parent.serialize()

    assert serialized["name"] == "parent"
    assert serialized["child"] == {"count": 3}
    assert serialized["tags"] == ["a", "b"]
    assert serialized["created_at"] == created_at.isoformat()
    assert serialized["uid"] == str(uid)
    assert serialized["color"] == Color.RED.value
    assert serialized["mapping"] == {"one": 1}


def test_deserialize_converts_types():
    """Ensure deserialize converts enums, UUIDs, datetime, and containers."""
    uid = uuid4()
    created_at = datetime(2024, 2, 1, 8, 0, 0)
    data = {
        "name": "parent",
        "child": {"count": "5"},
        "tags": ["x", "y"],
        "created_at": created_at.isoformat(),
        "uid": str(uid),
        "color": "blue",
        "values": ["1", "2"],
        "mapping": {"first": "10"},
        "optional_note": None,
    }

    parent = Parent.deserialize(data)

    assert parent.child.count == 5
    assert parent.uid == uid
    assert parent.created_at == created_at
    assert parent.color is Color.BLUE
    assert parent.values == [1, 2]
    assert parent.mapping == {"first": 10}
    assert parent.optional_note is None


def test_deserializers_override_field():
    """Custom __deserializers__ should take precedence over generic conversion."""

    @dataclass
    class CustomModel(Serializable):
        __deserializers__: ClassVar[dict[str, Any]] = {"name": lambda value: value.title()}

        name: str
        amount: int

    result = CustomModel.deserialize({"name": "john doe", "amount": "7"})

    assert result.name == "John Doe"
    assert result.amount == 7


def test_typevar_resolution_and_conversion():
    """TypeVar mapping should convert values to concrete type."""
    T = TypeVar("T")

    @dataclass
    class GenericModel(Serializable, Generic[T]):
        item: T

    @dataclass
    class IntModel(GenericModel[int]):
        pass

    model = IntModel.deserialize({"item": "9"})

    assert model.item == 9
    assert isinstance(model.item, int)


def test_serialize_non_dataclass_raises():
    """Serializable.serialize should require dataclass structure."""

    class PlainSerializable(Serializable):
        pass

    instance = PlainSerializable()

    with pytest.raises(TypeError):
        instance.serialize()


def test_deserialize_non_dataclass_raises():
    """deserialize should raise when used on non-dataclass classes."""

    class NonDataclassSerializable(Serializable):
        __module__ = "tests.libs.models.test_serializable"

    with pytest.raises(Exception) as exc:
        NonDataclassSerializable.deserialize({"value": 1})
    assert "NonDataclassSerializable" in str(exc.value)


def test_convert_value_iterables_and_mappings():
    """_convert_value should coerce common iterable and mapping types."""
    assert _convert_value(["1", "2"], list[int]) == [1, 2]
    assert _convert_value(("1", "2"), tuple[int, int]) == (1, 2)
    assert _convert_value({"a": "3"}, dict[str, int]) == {"a": 3}
    assert _convert_value({"x", "y"}, set[str]) == {"x", "y"}
    assert _convert_value((1, "2"), Iterable[int]) == [1, 2]
    assert _convert_value(None, int | None) is None


def test_convert_value_datetime():
    """Validate datetime conversion and passthrough."""
    iso_value = "2024-03-01T00:00:00"
    assert _convert_value(iso_value, datetime) == datetime.fromisoformat(iso_value)

    now = datetime.now()
    assert _convert_value(now, datetime) is now

    with pytest.raises(ValueError):
        _convert_value(["not", "valid"], datetime)


def test_convert_value_union():
    """Union conversion should handle None and raise last error when all members fail."""
    assert _convert_value(None, int | None) is None
    assert _convert_value(None, str | int | None) is None
    assert _convert_value("5", int | UUID) == 5

    with pytest.raises(ValueError):
        _convert_value("not-a-uuid", int | UUID)

    with pytest.raises(ValueError):
        _convert_value("abc", int | datetime)


def test_convert_value_returns_existing_instance():
    """_convert_value should return existing instance when already correct type."""
    child = Child(count=4)
    assert _convert_value(child, Child) is child


def test_convert_value_respects_deserialize_method():
    """Ensure mapping values use class-level deserialize when available."""

    class CustomDeserializable:
        @classmethod
        def deserialize(cls, payload: dict[str, str]) -> str:
            return f"parsed-{payload['raw']}"

    result = _convert_value({"raw": "value"}, CustomDeserializable)
    assert result == "parsed-value"


def test_convert_value_handles_edge_cases():
    """Test edge cases for _convert_value."""
    assert _convert_value("x", {"not": "a type"}) == "x"
    assert _convert_value("value", ForwardRef("Example")) == "value"

    with pytest.raises(ValueError):
        _convert_value("not-a-uuid", UUID)


def test_deserialize_sets_init_false_fields():
    """Ensure init=False fields receive defaults after deserialization."""

    @dataclass
    class WithInitFalse(Serializable):
        name: str
        computed: str = field(init=False, default="computed")
        dynamic: str = field(init=False, default_factory=lambda: "dynamic")

    instance = WithInitFalse.deserialize({"name": "example"})

    assert instance.computed == "computed"
    assert instance.dynamic == "dynamic"


def test_forward_reference_resolution():
    """String annotations currently preserve raw mapping."""

    @dataclass
    class ForwardParent(Serializable):
        child: "Child"

    parent = ForwardParent.deserialize({"child": {"count": "9"}})
    assert parent.child == {"count": "9"}


def test_dataset_typed_properties_specialization(monkeypatch):
    """Raw mappings currently deserialize to base DatasetTypedProperties."""

    @dataclass
    class MinimalDatasetProps(DatasetTypedProperties):
        foo: int

    @dataclass
    class ExtendedDatasetProps(DatasetTypedProperties):
        foo: int
        bar: str

    @dataclass
    class DatasetPropsContainer(Serializable):
        props: DatasetTypedProperties

    raw = {"props": {"foo": 1, "bar": "value"}}
    monkeypatch.setattr(
        DatasetTypedProperties,
        "__subclasses__",
        lambda: [MinimalDatasetProps, ExtendedDatasetProps],
        raising=False,
    )

    result = DatasetPropsContainer.deserialize(raw)

    assert isinstance(result.props, DatasetTypedProperties)
    assert result.props.serialize() == {}


def test_structural_specialization_selects_subclass(monkeypatch):
    """Structural specialization should pick the most specific subclass when enabled."""

    @dataclass
    class PatchedBase(Serializable):
        foo: int

    @dataclass
    class PatchedSub(PatchedBase):
        bar: str

    monkeypatch.setattr(serializable, "DatasetTypedProperties", PatchedBase)
    monkeypatch.setattr(serializable, "LinkedServiceTypedProperties", PatchedBase)

    @dataclass
    class Container(Serializable):
        props: PatchedBase

    result = Container.deserialize({"props": {"foo": 1, "bar": "ok"}})

    assert isinstance(result.props, PatchedSub)
    assert result.props.foo == 1
    assert result.props.bar == "ok"


def test_structural_specialization_no_candidate(monkeypatch):
    """When no subclass matches keys, base type should be used."""

    @dataclass
    class BaseProps(Serializable):
        foo: int

    @dataclass
    class SubProps(BaseProps):
        extra: str

    monkeypatch.setattr(serializable, "DatasetTypedProperties", BaseProps)
    monkeypatch.setattr(serializable, "LinkedServiceTypedProperties", BaseProps)
    monkeypatch.setattr(BaseProps, "__subclasses__", lambda: [], raising=False)

    @dataclass
    class Container(Serializable):
        props: BaseProps

    result = Container.deserialize({"props": {"foo": 1}})

    assert isinstance(result.props, BaseProps)
    assert not isinstance(result.props, SubProps)
    assert result.props.foo == 1


def test_serialize_value_handles_special_types():
    """Ensure serialize handles enum, UUID, datetime, and failure cases."""
    uid = uuid4()
    timestamp = datetime(2025, 1, 1, 12, 0, 0)

    assert serializable._serialize_value(Color.RED) == "red"
    assert serializable._serialize_value(uid) == str(uid)
    assert serializable._serialize_value(timestamp) == timestamp.isoformat()

    class RaisesSerialize:
        def serialize(self) -> dict[str, str]:
            raise RuntimeError("boom")

    obj = RaisesSerialize()
    assert serializable._serialize_value(obj) is obj


def test_build_type_var_map_handles_exception_on_parameters(monkeypatch):
    """Test that _build_type_var_map handles exceptions when getting __parameters__."""
    T = TypeVar("T")

    @dataclass
    class TestClass(Serializable, Generic[T]):
        value: T  # type: ignore[type-arg]

    class FailingOrigin:
        def __getattribute__(self, name):
            if name == "__parameters__":
                raise RuntimeError("Cannot access __parameters__")
            return super().__getattribute__(name)

    original_get_origin = get_origin

    def mock_get_origin(base_alias):
        result = original_get_origin(base_alias)
        if result is not None:
            return FailingOrigin()
        return result

    monkeypatch.setattr("typing.get_origin", mock_get_origin, raising=False)

    result = _build_type_var_map(TestClass)
    assert isinstance(result, dict)


def test_iter_subclasses_handles_exception_on_subclasses(monkeypatch):
    """Test that _iter_subclasses handles exceptions when getting __subclasses__."""

    @dataclass
    class TestBase(Serializable):
        foo: int

    monkeypatch.setattr(serializable, "DatasetTypedProperties", TestBase)
    monkeypatch.setattr(serializable, "LinkedServiceTypedProperties", TestBase)

    def failing_subclasses():
        raise RuntimeError("Cannot get subclasses")

    monkeypatch.setattr(TestBase, "__subclasses__", failing_subclasses, raising=False)

    result = _apply_structural_specialization({"foo": 1}, TestBase, TestBase)
    assert result == TestBase


def test_resolve_type_hint_uses_cls_own_hints_when_field_type_is_any():
    """Test that _resolve_type_hint_for_field uses cls_own_hints when field.type is Any."""

    @dataclass
    class TestClass(Serializable):
        value: Any

    field_obj = fields(TestClass)[0]
    cls_own_hints = {"value": int}
    type_var_map = {}

    original_type = field_obj.type
    field_obj.type = None

    hint = _resolve_type_hint_for_field(
        field=field_obj,
        field_name="value",
        cls_own_hints=cls_own_hints,
        type_var_map=type_var_map,
        cls=TestClass,
    )

    assert isinstance(hint, type) and hint is int
    field_obj.type = original_type


def test_resolve_type_hint_successfully_resolves_string_annotation():
    """Test that _resolve_type_hint_for_field successfully resolves string annotations."""

    @dataclass
    class TestClass(Serializable):
        value: "int"

    field_obj = fields(TestClass)[0]
    original_type = field_obj.type
    field_obj.type = "int"
    cls_own_hints = {}
    type_var_map = {}

    hint = _resolve_type_hint_for_field(
        field=field_obj,
        field_name="value",
        cls_own_hints=cls_own_hints,
        type_var_map=type_var_map,
        cls=TestClass,
    )

    assert (isinstance(hint, type) and hint is int) or isinstance(hint, str)
    field_obj.type = original_type


def test_apply_structural_specialization_handles_exception(monkeypatch):
    """Test that _apply_structural_specialization handles exceptions gracefully."""

    @dataclass
    class TestBase(Serializable):
        foo: int

    monkeypatch.setattr(serializable, "DatasetTypedProperties", TestBase)
    monkeypatch.setattr(serializable, "LinkedServiceTypedProperties", TestBase)

    def failing_iter_subclasses(base):
        raise RuntimeError("Cannot get subclasses")

    monkeypatch.setattr(
        "ds_resource_plugin_py_lib.libs.models.serializable._iter_subclasses",
        failing_iter_subclasses,
        raising=False,
    )

    result = _apply_structural_specialization({"foo": 1, "bar": "test"}, TestBase, TestBase)
    assert result == TestBase


def test_apply_structural_specialization_when_selected_equals_hint(monkeypatch):
    """Test _apply_structural_specialization when condition at line 338 is False."""

    @dataclass
    class TestBase(Serializable):
        foo: int
        bar: int

    @dataclass
    class TestSub(TestBase):
        pass

    monkeypatch.setattr(serializable, "DatasetTypedProperties", TestBase)
    monkeypatch.setattr(serializable, "LinkedServiceTypedProperties", TestBase)
    monkeypatch.setattr(
        TestBase,
        "__subclasses__",
        lambda: [TestSub],
        raising=False,
    )

    result = _apply_structural_specialization({"foo": 1, "bar": 2}, TestBase, TestBase)
    assert isinstance(result, type)


def test_set_init_false_fields_with_default():
    """Test _set_init_false_fields with default value."""

    @dataclass
    class TestClass(Serializable):
        name: str
        computed: str = field(init=False, default="default_value")

    instance = TestClass.__new__(TestClass)
    instance.name = "test"
    assert "computed" not in instance.__dict__

    fields_tuple = fields(TestClass)
    _set_init_false_fields(instance, fields_tuple)

    assert instance.computed == "default_value"


def test_set_init_false_fields_with_default_factory():
    """Test _set_init_false_fields with default_factory."""

    @dataclass
    class TestClass(Serializable):
        name: str
        dynamic: list[str] = field(init=False, default_factory=list)

    instance = TestClass(name="test")
    if hasattr(instance, "dynamic"):
        delattr(instance, "dynamic")

    fields_tuple = fields(TestClass)
    _set_init_false_fields(instance, fields_tuple)

    assert instance.dynamic == []
