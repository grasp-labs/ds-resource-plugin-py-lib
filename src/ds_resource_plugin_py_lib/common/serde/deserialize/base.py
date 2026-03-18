"""
**File:** ``base.py``
**Region:** ``ds_resource_plugin_py_lib/common/serde/deserialize``

Description
-----------
Base classes for deserializers.
"""

from dataclasses import dataclass, field
from typing import Any, Self

from ds_common_serde_py_lib import Serializable

from ..base import SerdeSettings


@dataclass(kw_only=True)
class DataDeserializer(Serializable):
    """
    Extensible class to deserialize dataset content.

    Not supposed to be used directly, but to be subclassed.
    """

    settings: SerdeSettings = field(default_factory=SerdeSettings)

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Self:
        serde_kwargs = {key: value for key, value in data.items() if key not in {"type", "version"}}
        if "settings" in serde_kwargs:
            return super().deserialize(serde_kwargs)
        return cls(**serde_kwargs)

    def __call__(self, value: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def get_next(self, _value: Any, **_kwargs: Any) -> bool:
        return False

    def get_end_cursor(self, _value: Any, **_kwargs: Any) -> str | None:
        return None
