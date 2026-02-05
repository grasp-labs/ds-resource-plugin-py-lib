"""
**File:** ``test_linked_service_base_abstracts.py``
**Region:** ``tests/common/resource/linked_service``

Description
-----------
Cover base `LinkedService` abstract-method NotImplementedError bodies.
"""

import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from ds_resource_plugin_py_lib.common.resource.linked_service.base import LinkedService, LinkedServiceSettings


@dataclass(kw_only=True)
class _DummySettings(LinkedServiceSettings):
    pass


@dataclass(kw_only=True)
class _DummyLinkedService(LinkedService[_DummySettings]):
    settings: _DummySettings

    @property
    def type(self):  # type: ignore[override]
        # Exercise base property body (raises NotImplementedError).
        return LinkedService.type.fget(self)  # type: ignore[misc]

    def connect(self) -> Any:
        return LinkedService.connect(self)  # type: ignore[misc]

    def test_connection(self) -> tuple[bool, str]:
        return LinkedService.test_connection(self)  # type: ignore[misc]

    def close(self) -> None:
        return LinkedService.close(self)  # type: ignore[misc]


class TestLinkedServiceBaseAbstractBodies:
    def test_linked_service_base_abstracts_raise_not_implemented(self):
        ls = _DummyLinkedService(
            id=uuid.uuid4(),
            name="test_linked_service",
            version="1.0.0",
            settings=_DummySettings(),
        )

        with pytest.raises(NotImplementedError):
            _ = ls.type
        with pytest.raises(NotImplementedError):
            ls.connect()
        with pytest.raises(NotImplementedError):
            ls.test_connection()
        with pytest.raises(NotImplementedError):
            ls.close()
