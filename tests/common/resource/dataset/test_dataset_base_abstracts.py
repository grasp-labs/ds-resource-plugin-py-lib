"""
**File:** ``test_dataset_base_abstracts.py``
**Region:** ``tests/common/resource/dataset``

Description
-----------
Cover ``OperationInfo`` auto-population and ``track_result`` decorator behaviour.
"""

import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import pandas as pd
import pytest

from ds_resource_plugin_py_lib.common.resource.dataset.base import (
    DatasetSettings,
    TabularDataset,
)
from ds_resource_plugin_py_lib.common.resource.dataset.enums import DatasetMethod
from ds_resource_plugin_py_lib.common.resource.dataset.result import OperationInfo
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
        return "dummy"

    @property
    def connection(self) -> Any:
        return None

    def connect(self) -> None:
        pass

    def test_connection(self) -> tuple[bool, str]:
        return (True, "")

    def close(self) -> None:
        pass


@dataclass(kw_only=True)
class _DummyDatasetSettings(DatasetSettings):
    pass


@dataclass(kw_only=True)
class _ConcreteDataset(TabularDataset[_DummyLinkedService, _DummyDatasetSettings, DataSerializer, DataDeserializer]):
    settings: _DummyDatasetSettings
    linked_service: _DummyLinkedService

    @property
    def type(self) -> StrEnum:  # type: ignore[override]
        class _T(StrEnum):
            TEST = "test"

        return _T.TEST

    def create(self) -> None:
        self.output = self.input.copy()

    def read(self) -> None:
        self.output = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})

    def update(self) -> None:
        self.output = self.input.copy()

    def upsert(self) -> None:
        self.output = self.input.copy()

    def delete(self) -> None:
        self.output = self.input.copy()

    def purge(self) -> None:
        pass

    def list(self) -> None:
        self.output = pd.DataFrame({"resource": ["table_a", "table_b"]})

    def rename(self) -> None:
        pass

    def close(self) -> None:
        pass


def _make_concrete() -> _ConcreteDataset:
    return _ConcreteDataset(
        id=uuid.uuid4(),
        name="concrete",
        version="1.0.0",
        settings=_DummyDatasetSettings(),
        linked_service=_DummyLinkedService(
            id=uuid.uuid4(),
            name="ls",
            version="1.0.0",
            settings=_DummyLinkedServiceSettings(),
        ),
    )


class TestOperationInfoField:
    def test_result_is_operation_result_on_init(self):
        ds = _make_concrete()
        assert isinstance(ds.operation, OperationInfo)
        assert ds.operation.method is None


class TestTrackResultDecorator:
    def test_timing_is_populated(self):
        ds = _make_concrete()
        ds.read()

        assert ds.operation.method == DatasetMethod.READ
        assert ds.operation.started_at is not None
        assert ds.operation.ended_at is not None
        assert ds.operation.duration_ms >= 0
        assert ds.operation.ended_at >= ds.operation.started_at

    def test_row_count_auto_derived(self):
        ds = _make_concrete()
        ds.input = pd.DataFrame({"id": [1, 2]})
        ds.create()

        assert ds.operation.row_count == 2

    def test_row_count_from_read(self):
        ds = _make_concrete()
        ds.read()

        assert ds.operation.row_count == 3

    def test_schema_auto_derived_on_read(self):
        ds = _make_concrete()
        ds.read()

        assert ds.operation.schema is not None
        assert "id" in ds.operation.schema
        assert "name" in ds.operation.schema

    def test_schema_auto_derived_on_list(self):
        ds = _make_concrete()
        ds.list()

        assert ds.operation.schema is not None
        assert "resource" in ds.operation.schema

    def test_schema_derived_on_write(self):
        ds = _make_concrete()
        ds.input = pd.DataFrame({"id": [1]})
        ds.create()

        assert ds.operation.schema is not None
        assert "id" in ds.operation.schema

    def test_result_reset_on_each_call(self):
        ds = _make_concrete()
        ds.read()
        assert ds.operation.method == DatasetMethod.READ

        ds.input = pd.DataFrame({"id": [1]})
        ds.create()
        assert ds.operation.method == DatasetMethod.CREATE

    def test_provider_can_override_row_count(self):
        """Provider sets row_count explicitly; decorator should not overwrite."""

        @dataclass(kw_only=True)
        class _CustomDataset(_ConcreteDataset):
            def create(self) -> None:
                self.output = self.input.copy()
                self.operation.row_count = 999

        ds = _CustomDataset(
            id=uuid.uuid4(),
            name="custom",
            version="1.0.0",
            settings=_DummyDatasetSettings(),
            linked_service=_DummyLinkedService(
                id=uuid.uuid4(),
                name="ls",
                version="1.0.0",
                settings=_DummyLinkedServiceSettings(),
            ),
        )
        ds.input = pd.DataFrame({"id": [1]})
        ds.create()

        assert ds.operation.row_count == 999

    def test_timing_populated_even_on_failure(self):
        @dataclass(kw_only=True)
        class _FailingDataset(_ConcreteDataset):
            def create(self) -> None:
                raise RuntimeError("boom")

        ds = _FailingDataset(
            id=uuid.uuid4(),
            name="failing",
            version="1.0.0",
            settings=_DummyDatasetSettings(),
            linked_service=_DummyLinkedService(
                id=uuid.uuid4(),
                name="ls",
                version="1.0.0",
                settings=_DummyLinkedServiceSettings(),
            ),
        )
        with pytest.raises(RuntimeError, match="boom"):
            ds.create()

        assert ds.operation.method == DatasetMethod.CREATE
        assert ds.operation.started_at is not None
        assert ds.operation.ended_at is not None
        assert ds.operation.duration_ms >= 0
