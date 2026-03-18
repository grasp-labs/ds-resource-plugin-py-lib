"""
**File:** ``base.py``
**Region:** ``ds_resource_plugin_py_lib/common/serde/serialize``

Description
-----------
Base classes for serializers.
"""

from dataclasses import dataclass, field
from typing import Any, NamedTuple

from ds_common_serde_py_lib import Serializable

from ..base import SerdeSettings


class SerializerInfo(NamedTuple):
    """
    NamedTuple that represents serializer registration metadata.
    """

    type: str
    name: str
    class_name: str
    version: str
    description: str | None = None

    @property
    def key(self) -> tuple[str, str]:
        """
        Return the composite key (type, version) for dictionary lookups.

        Returns:
            A tuple containing the type and version.
        """
        return (self.type, self.version)


@dataclass(kw_only=True)
class DataSerializer(Serializable):
    """
    Extensible class to serialize dataset content.

    Convert obj to bytes.

    Not supposed to be used directly, but to be subclassed.
    """

    settings: SerdeSettings = field(default_factory=SerdeSettings)

    def __call__(self, obj: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
