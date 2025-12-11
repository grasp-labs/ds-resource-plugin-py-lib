"""Serializable mixin for dataclasses.

This module provides a lightweight ``Serializable`` mixin that adds
``serialize`` and ``deserialize`` helpers to Python dataclasses. It aims to be
safe at import time and minimally opinionated, while still covering common
use-cases:

- Enums are serialized to their ``.value`` and parsed back using the Enum type
  when available.
- UUIDs are serialized to their canonical string form and parsed back to
  ``uuid.UUID`` when annotated as such.
- Nested dataclasses are recursively (de)serialized. For non-dataclass objects
  that provide ``serialize``/``deserialize``, those are used.
- Typed containers (``list``, ``tuple``, ``set``, ``dict``) are handled using
  type annotations where feasible.

Customization is supported via an optional ``__deserializers__`` mapping on the
dataclass: ``{"field_name": callable}`` where the callable converts the raw
input value into the desired field value.
"""

import logging
import sys
from collections.abc import Iterable, Mapping
from dataclasses import MISSING, is_dataclass
from dataclasses import fields as dc_fields
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, TypeVar, cast, get_args, get_origin, get_type_hints
from uuid import UUID

from ds_common_logger_py_lib import Logger, LoggingMixin

# Import here to avoid circular imports - these are only used conditionally
try:
    from ...common.resource.dataset.base import DatasetTypedProperties
    from ...common.resource.linked_service.base import LinkedServiceTypedProperties
except ImportError:
    DatasetTypedProperties = None  # type: ignore[assignment,misc]
    LinkedServiceTypedProperties = None  # type: ignore[assignment,misc]

# Concrete runtime type for typing.TypeVar instances
TypeVarType = type(TypeVar("_T_RUNTIME_MARKER_"))


T = TypeVar("T", bound="Serializable")


logger = Logger.get_logger(__name__)


class Serializable(LoggingMixin):
    """Mixin providing ``serialize``/``deserialize`` for dataclasses.

    Add this as a base class to a ``@dataclass`` to gain:

    - ``serialize(self) -> dict``: Convert the instance into a plain Python
      structure suitable for JSON encoding.
    - ``deserialize(cls, data) -> cls``: Construct an instance from a mapping,
      with best-effort conversions using type hints.

    Advanced control: define ``__deserializers__`` on your dataclass to supply
    per-field converter callables that receive the raw value and return a
    properly typed value.
    """

    # Map of field name -> converter function(value) -> converted value
    __deserializers__: ClassVar[dict[str, Any]] = {}
    log_level = logging.DEBUG

    def serialize(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the dataclass.

        - Enums become their ``.value``
        - UUIDs become strings
        - Nested dataclasses are serialized recursively
        - Lists, sets, tuples and dicts are traversed recursively
        """
        result = _serialize_value(self)
        # For dataclasses, _serialize_value always returns a dict
        if not isinstance(result, dict):
            raise TypeError(f"Expected dict, got {type(result)}")
        return result

    @classmethod
    def deserialize(cls: type[T], data: Mapping[str, Any]) -> T:  # noqa: PLR0912, PLR0915
        """Create an instance from a mapping.

        The method performs best-effort conversions guided by type hints:
        - Enums via constructor from value
        - UUIDs from strings
        - Nested dataclasses that expose ``deserialize``
        - Annotated containers (lists/tuples/sets/dicts)

        If a ``__deserializers__`` dict is present, its field-specific
        functions take precedence over generic conversions.

        Raises:
            TypeError: If ``cls`` is not a dataclass.
        """

        kwargs: dict[str, Any] = {}
        deserializers = getattr(cls, "__deserializers__", {}) or {}

        # Resolve generic TypeVars used by this class through its specialized bases
        # Example: class FooModel(Generic[T]); class BarModel(FooModel[Concrete])
        # We map T -> Concrete so hints using T can be concretized at runtime
        type_var_map: dict[Any, Any] = {}
        for base_alias in getattr(cls, "__orig_bases__", []) or []:
            origin = get_origin(base_alias)
            args = get_args(base_alias)
            try:
                params = getattr(origin, "__parameters__", ())
            except Exception:
                params = ()
            for param, arg in zip(params or (), args or (), strict=True):
                type_var_map[param] = arg

        # Try to get type hints from the class itself (may fail due to TypeVar issues)
        # We primarily rely on dataclass field types (f.type) which are more reliable
        cls_own_hints: dict[str, Any] = {}
        try:
            module = sys.modules.get(cls.__module__)
            module_globals = vars(module) if module is not None else {}
            cls_own_hints = (
                get_type_hints(
                    cls,
                    globalns=module_globals,
                    localns=None,
                )
                or {}
            )
        except Exception as exc:
            logger.debug("Failed to get type hints for %s: %s", cls.__name__, exc)

        try:
            class_fields = dc_fields(cast("Any", cls))
        except Exception as exc:
            raise Exception(
                str(exc),
                {
                    "type": type(exc).__name__,
                    "class_name": cls.__name__,
                },
            ) from exc

        def _iter_subclasses(base: type) -> Iterable[type]:
            seen: set[type] = set()
            stack: list[type] = [base]
            while stack:
                current = stack.pop()
                for sub in getattr(current, "__subclasses__", lambda: [])():
                    if sub not in seen:
                        seen.add(sub)
                        yield sub
                        stack.append(sub)

        for f in class_fields:
            name = f.name
            if name not in data:
                continue

            raw_value = data[name]

            # Field-specific converter takes precedence
            converter = deserializers.get(name)
            if callable(converter):
                kwargs[name] = converter(raw_value)
                continue

            # Resolve type hint: prioritize dataclass field type (f.type) as it's most reliable
            # for concrete class annotations. Fall back to cls_own_hints if f.type is a TypeVar.
            if f.type and not isinstance(f.type, TypeVarType) and f.type is not Any:
                hint = f.type
            elif name in cls_own_hints:
                hint = cls_own_hints[name]
            else:
                hint = f.type

            # Resolve TypeVar if needed
            if isinstance(hint, TypeVarType):
                hint = type_var_map.get(hint, getattr(hint, "__bound__", Any))

            # Handle string annotations from __future__ import annotations
            if isinstance(hint, str):
                module = sys.modules.get(cls.__module__)
                module_globals = vars(module) if module is not None else {}
                try:
                    resolved_hints = get_type_hints(
                        cls,
                        globalns=module_globals,
                        localns={},
                    )
                    if name in resolved_hints:
                        hint = resolved_hints[name]
                except Exception as exc:
                    logger.debug(
                        "Failed to resolve type hint '%s' for %s.%s: %s",
                        hint,
                        cls.__name__,
                        name,
                        exc,
                    )

            # Structural specialization: only for base classes that need subclass selection
            # If hint is already a concrete class (e.g., HttpDatasetTypedProperties), use it directly
            if (
                isinstance(raw_value, Mapping)
                and isinstance(hint, type)
                and issubclass(hint, Serializable)
                and DatasetTypedProperties is not None
                and LinkedServiceTypedProperties is not None
                and hint in (DatasetTypedProperties, LinkedServiceTypedProperties)
            ):
                try:
                    subclasses = list(_iter_subclasses(hint))
                    if subclasses:
                        value_keys = set(dict(raw_value).keys())
                        candidates = [sub for sub in subclasses if value_keys.issubset({fld.name for fld in dc_fields(sub)})]
                        if candidates:
                            # Prefer same-module subclasses, then most specific (most fields)
                            same_module = [c for c in candidates if getattr(c, "__module__", None) == cls.__module__]
                            pool = same_module or candidates
                            selected = max(
                                pool,
                                key=lambda c: len(getattr(c, "__dataclass_fields__", {}) or {}),
                            )
                            selected_fields = len(getattr(selected, "__dataclass_fields__", {}) or {})
                            hint_fields = len(getattr(hint, "__dataclass_fields__", {}) or {})
                            if selected != hint and selected_fields > hint_fields:
                                hint = selected
                except Exception:  # nosec
                    pass
            kwargs[name] = _convert_value(raw_value, hint)

        instance = cls(**kwargs)

        # Ensure fields with init=False and defaults are set
        for f in class_fields:
            if not f.init and not hasattr(instance, f.name):
                if f.default is not MISSING:
                    setattr(instance, f.name, f.default)
                elif f.default_factory is not MISSING:
                    setattr(instance, f.name, f.default_factory())

        return instance


def _serialize_value(value: Any) -> Any:
    """Recursively serialize common Python types and dataclasses.

    Returns a structure comprised of dicts, lists, and primitives that can be
    JSON-encoded without custom hooks.
    """
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        result: dict[str, Any] = {}
        for f in dc_fields(value):
            result[f.name] = _serialize_value(getattr(value, f.name))
        return result
    if hasattr(value, "serialize") and callable(value.serialize):
        try:
            return value.serialize()
        except Exception as exc:
            # Log at debug level - this is expected for objects that may not serialize properly
            # We fall through to other serialization strategies
            logger.debug("Failed to serialize object %s: %s", type(value).__name__, exc)
    if isinstance(value, Mapping):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize_value(v) for v in value]
    return value


def _convert_value(value: Any, type_hint: Any) -> Any:  # noqa: PLR0912
    """Convert ``value`` into the type described by ``type_hint`` using a generic strategy.

    Rules of conversion:
    - If the value already matches the target type, return it.
    - For ``Enum`` subclasses, construct using the enum type.
    - For classes providing ``deserialize`` and when value is a mapping, call ``deserialize``.
    - For dataclasses (that don't expose ``deserialize``), leave to caller or return as-is.
    - For plain classes (including ``uuid.UUID``), call the type with the value as a single argument.
      If construction fails, raise the error instead of returning the raw value.
    - Containers (list/tuple/set) and mappings are converted recursively based on their inner type args.
    - For ``Union`` (including ``Optional``), attempt each member type until one succeeds.

    Forward references are intentionally left unresolved to avoid import-time cycles.
    """
    if value is None or type_hint is Any:
        return value

    origin = get_origin(type_hint)
    args = get_args(type_hint)

    # typing.Optional[T] appears as Union[T, NoneType]
    if origin is None and isinstance(type_hint, type):
        # If it already matches the desired type, keep it
        if isinstance(value, type_hint):
            return value

        # Enum types: construct via enum constructor
        if issubclass(type_hint, Enum):
            return type_hint(value)

        # If the target type exposes a deserialize and value is a mapping, use it
        if isinstance(value, Mapping) and hasattr(type_hint, "deserialize") and callable(type_hint.deserialize):
            return type_hint.deserialize(value)

        # Special handling for datetime
        if type_hint is datetime:
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            elif isinstance(value, datetime):
                return value
            else:
                raise ValueError(f"Cannot convert {type(value)} to datetime")

        # Generic constructor path (covers types like uuid.UUID, str, int, float, etc.)
        try:
            if isinstance(type_hint, type):
                # type_hint is a type, so it can be called with value
                return type_hint(value)  # type: ignore[call-arg]
            else:
                raise ValueError(f"Cannot instantiate non-type {type_hint}")
        except Exception as exc:
            # Leave unresolved forward-refs/types to caller; otherwise fail loudly
            raise exc

    if origin in (list, tuple, set, Iterable):
        inner = args[0] if args else Any
        converted_list = [_convert_value(v, inner) for v in (list(value) if not isinstance(value, list) else value)]
        if origin is list or origin is Iterable:
            return converted_list
        if origin is tuple:
            return tuple(converted_list)
        if origin is set:
            return set(converted_list)
        return converted_list

    if origin in (dict, dict, Mapping):
        key_t = args[0] if len(args) == 2 else Any
        val_t = args[1] if len(args) == 2 else Any
        return {_convert_value(k, key_t): _convert_value(v, val_t) for k, v in dict(value).items()}

    # typing.Union[...] (including Optional)
    if origin is getattr(__import__("typing"), "Union", None):
        last_err: Exception | None = None
        for arg in args:
            if arg is type(None):
                if value is None:
                    return None
                continue
            try:
                return _convert_value(value, arg)
            except Exception as exc:
                last_err = exc
                continue
        if last_err is not None:
            raise last_err
        return value

    # Unresolved forward refs will come through as str or typing.ForwardRef; leave as-is
    return value
