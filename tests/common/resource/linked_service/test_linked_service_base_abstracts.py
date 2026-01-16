"""
**File:** ``test_linked_service_base_abstracts.py``
**Region:** ``tests/common/resource/linked_service``

Description
-----------
Cover base `LinkedService` abstract-method NotImplementedError bodies.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from ds_resource_plugin_py_lib.common.resource.linked_service.base import LinkedService, LinkedServiceTypedProperties


@dataclass(kw_only=True)
class _DummyProps(LinkedServiceTypedProperties):
    pass


@dataclass(kw_only=True)
class _DummyLinkedService(LinkedService[_DummyProps]):
    typed_properties: _DummyProps

    @property
    def kind(self):  # type: ignore[override]
        # Exercise base property body (raises NotImplementedError).
        return LinkedService.kind.fget(self)  # type: ignore[misc]

    def connect(self) -> Any:
        return LinkedService.connect(self)  # type: ignore[misc]

    def test_connection(self) -> tuple[bool, str]:
        return LinkedService.test_connection(self)  # type: ignore[misc]

    def close(self) -> None:
        return LinkedService.close(self)  # type: ignore[misc]


class TestLinkedServiceBaseAbstractBodies:
    def test_linked_service_base_abstracts_raise_not_implemented(self):
        ls = _DummyLinkedService(typed_properties=_DummyProps())

        with pytest.raises(NotImplementedError):
            _ = ls.kind
        with pytest.raises(NotImplementedError):
            ls.connect()
        with pytest.raises(NotImplementedError):
            ls.test_connection()
        with pytest.raises(NotImplementedError):
            ls.close()
