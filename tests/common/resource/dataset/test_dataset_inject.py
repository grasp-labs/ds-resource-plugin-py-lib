"""
File: test_dataset_inject.py
Description: Tests for Dataset._inject_linked_service helper.
Region: packages/shared
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock

from ds_resource_plugin_py_lib.common.resource.dataset.base import Dataset, DatasetTypedProperties
from ds_resource_plugin_py_lib.common.resource.linked_service.base import LinkedService


@dataclass
class DummyLinkedService(LinkedService[DatasetTypedProperties]):
    """Minimal linked service for injection testing."""

    typed_properties: DatasetTypedProperties

    @property
    def kind(self) -> Any:
        return "KIND"

    def connect(self) -> Any:
        return None

    def test_connection(self) -> tuple[bool, str]:
        return True, "ok"


@dataclass
class DummyDataset(Dataset[DummyLinkedService, DatasetTypedProperties]):
    """Minimal dataset exposing kind."""

    typed_properties: DatasetTypedProperties
    linked_service: DummyLinkedService

    @property
    def kind(self) -> str:
        return "KIND"

    def create(self, **kwargs: Any) -> Any:
        return None

    def read(self, **kwargs: Any) -> Any:
        return None

    def delete(self, **kwargs: Any) -> Any:
        return None

    def update(self, **kwargs: Any) -> Any:
        return None

    def rename(self, **kwargs: Any) -> Any:
        return None


def test_inject_linked_service_sets_attribute():
    """_inject_linked_service should set linked_service on dataset."""
    ds = DummyDataset(
        typed_properties=DatasetTypedProperties(),
        linked_service=Mock(spec=DummyLinkedService),
    )

    new_service = DummyLinkedService(typed_properties=DatasetTypedProperties())
    ds._inject_linked_service(new_service)

    assert ds.linked_service is new_service
