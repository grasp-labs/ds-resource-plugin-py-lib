"""
**File:** ``test_dataset_base_abstracts.py``
**Region:** ``tests/common/resource/dataset``

Description
-----------
Cover base `Dataset` abstract-method NotImplementedError bodies.
"""

import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import pytest

from ds_resource_plugin_py_lib.common.resource.dataset.base import Dataset, DatasetSettings
from ds_resource_plugin_py_lib.common.resource.linked_service.base import LinkedService, LinkedServiceSettings
from ds_resource_plugin_py_lib.common.serde.deserialize.base import DataDeserializer
from ds_resource_plugin_py_lib.common.serde.serialize.base import DataSerializer


@dataclass(kw_only=True)
class _DummyLinkedServiceSettings(LinkedServiceSettings):
    pass


@dataclass(kw_only=True)
class _DummyLinkedService(LinkedService[_DummyLinkedServiceSettings]):
    settings: _DummyLinkedServiceSettings

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


@dataclass(kw_only=True)
class _DummyDatasetSettings(DatasetSettings):
    pass


@dataclass(kw_only=True)
class _DummyDataset(Dataset[_DummyLinkedService, _DummyDatasetSettings, DataSerializer, DataDeserializer]):
    id: uuid.UUID
    name: str
    description: str | None = None
    settings: _DummyDatasetSettings
    linked_service: _DummyLinkedService

    @property
    def type(self) -> StrEnum:
        # Exercise base property body (raises NotImplementedError).
        return Dataset.type.fget(self)  # type: ignore[misc]

    def create(self, **kwargs: Any) -> Any:
        return Dataset.create(self, **kwargs)  # type: ignore[misc]

    def read(self, **kwargs: Any) -> Any:
        return Dataset.read(self, **kwargs)  # type: ignore[misc]

    def delete(self, **kwargs: Any) -> Any:
        return Dataset.delete(self, **kwargs)  # type: ignore[misc]

    def update(self, **kwargs: Any) -> Any:
        return Dataset.update(self, **kwargs)  # type: ignore[misc]

    def rename(self, **kwargs: Any) -> Any:
        return Dataset.rename(self, **kwargs)  # type: ignore[misc]

    def close(self) -> None:
        return Dataset.close(self)  # type: ignore[misc]


class TestDatasetBaseAbstractBodies:
    def test_dataset_base_abstracts_raise_not_implemented(self):
        ds = _DummyDataset(
            id=uuid.uuid4(),
            name="test_dataset",
            settings=_DummyDatasetSettings(),
            linked_service=_DummyLinkedService(
                id=uuid.uuid4(),
                name="test_linked_service",
                settings=_DummyLinkedServiceSettings(),
            ),
        )

        with pytest.raises(NotImplementedError):
            _ = ds.type
        with pytest.raises(NotImplementedError):
            ds.create()
        with pytest.raises(NotImplementedError):
            ds.read()
        with pytest.raises(NotImplementedError):
            ds.delete()
        with pytest.raises(NotImplementedError):
            ds.update()
        with pytest.raises(NotImplementedError):
            ds.rename()
        with pytest.raises(NotImplementedError):
            ds.close()
