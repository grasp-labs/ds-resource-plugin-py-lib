"""
**File:** ``test_dataset_row_schema_validation.py``
**Region:** ``tests/common/resource/dataset``

Description
-----------
Cover ``TabularDataset.row_schema`` declaration and the
``_validate_output_row_schema`` hook wired into ``track_result``.

``row_schema`` is a portable, engine-agnostic table/row data contract (e.g.
``"int64"``, ``"string"``) -- not a place to write pandas/PyArrow
implementation details like ``"int64[pyarrow]"``, and not to be confused
with a JSON Schema (see ``DATASET_CONTRACT.md`` -- "Schema and Dataclass
Alignment", which validates a dataset's *construction payload*, a different
concept). See ``test_dataset_dtype_normalization.py`` for unit coverage of
the normalization rules themselves; this file covers how that normalization
is wired into dataset method calls end-to-end.
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
from ds_resource_plugin_py_lib.common.resource.dataset.errors import RowSchemaValidationError
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
class _RowSchemaDataset(
    TabularDataset[_DummyLinkedService, _DummyDatasetSettings, DataSerializer, DataDeserializer]
):
    settings: _DummyDatasetSettings
    linked_service: _DummyLinkedService

    @property
    def type(self) -> StrEnum:  # type: ignore[override]
        class _T(StrEnum):
            TEST = "test"

        return _T.TEST

    def create(self) -> None:
        if self.input is None or len(self.input) == 0:
            return
        self.output = self.input.copy()

    def read(self) -> None:
        self.output = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})

    def update(self) -> None:
        if self.input is None or len(self.input) == 0:
            return
        self.output = self.input.copy()

    def upsert(self) -> None:
        if self.input is None or len(self.input) == 0:
            return
        self.output = self.input.copy()

    def delete(self) -> None:
        if self.input is None or len(self.input) == 0:
            return
        self.output = self.input.copy()

    def purge(self) -> None:
        pass

    def list(self) -> None:
        self.output = pd.DataFrame({"resource": ["table_a", "table_b"]})

    def rename(self) -> None:
        pass

    def close(self) -> None:
        pass


def _make(row_schema: dict[str, str] | None = None) -> _RowSchemaDataset:
    return _RowSchemaDataset(
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
        row_schema=row_schema,
    )


class TestRowSchemaField:
    def test_defaults_to_none(self):
        ds = _make()
        assert ds.row_schema is None

    def test_can_be_declared_with_portable_type_names(self):
        ds = _make(row_schema={"id": "int64", "name": "string"})
        assert ds.row_schema == {"id": "int64", "name": "string"}


class TestRowSchemaValidation:
    def test_no_validation_when_row_schema_not_declared(self):
        ds = _make()
        ds.read()  # not raising is the assertion

        assert ds.operation.success is True

    def test_matching_row_schema_passes_with_portable_type_names(self):
        """The declared row schema never needs to know pandas produces
        "int64[pyarrow]"/"string[pyarrow]" internally -- plain portable
        names are normalized to match."""
        ds = _make(row_schema={"id": "int64", "name": "string"})
        ds.read()

        assert ds.operation.success is True

    def test_legacy_pyarrow_suffixed_row_schema_still_works(self):
        """Backward compatible: row schemas written with pandas-specific
        "[pyarrow]"-suffixed strings (the old, leaky contract) still
        normalize and validate correctly end-to-end."""
        ds = _make(row_schema={"id": "int64[pyarrow]", "name": "string[pyarrow]"})
        ds.read()

        assert ds.operation.success is True

    def test_mismatched_column_raises(self):
        ds = _make(row_schema={"id": "int64", "email": "string"})

        with pytest.raises(RowSchemaValidationError):
            ds.read()

        assert ds.operation.success is False
        assert ds.operation.error is not None
        assert ds.operation.error.code == "DS_DATASET_ROW_SCHEMA_VALIDATION_ERROR"

    def test_mismatched_type_raises(self):
        ds = _make(row_schema={"id": "string", "name": "string"})

        with pytest.raises(RowSchemaValidationError) as exc_info:
            ds.read()

        assert exc_info.value.details["expected"] == {"id": "string", "name": "string"}
        assert exc_info.value.details["actual"]["id"] != "string"

    def test_empty_output_skips_validation(self):
        @dataclass(kw_only=True)
        class _EmptyReadDataset(_RowSchemaDataset):
            def read(self) -> None:
                self.output = pd.DataFrame()

        ds = _EmptyReadDataset(
            id=uuid.uuid4(),
            name="empty",
            version="1.0.0",
            settings=_DummyDatasetSettings(),
            linked_service=_DummyLinkedService(
                id=uuid.uuid4(),
                name="ls",
                version="1.0.0",
                settings=_DummyLinkedServiceSettings(),
            ),
            row_schema={"id": "int64", "name": "string"},
        )
        ds.read()

        assert ds.operation.success is True

    def test_list_is_not_row_schema_validated(self):
        """`list()` returns resource-discovery metadata, not dataset rows."""
        ds = _make(row_schema={"id": "int64", "name": "string"})
        ds.list()

        assert ds.operation.success is True

    def test_create_is_validated(self):
        """create() is still row-schema-validated (partial-match mode):
        missing the declared "name" column is fine, but the undeclared
        "wrong" column is still flagged."""
        ds = _make(row_schema={"id": "int64", "name": "string"})
        ds.input = pd.DataFrame({"id": [1], "wrong": ["x"]})

        with pytest.raises(RowSchemaValidationError):
            ds.create()

    def test_operation_schema_stays_raw_and_unnormalized(self):
        """`self.operation.schema` is a separate, general-purpose diagnostic
        field (always the raw PyArrow-backend string) -- normalization only
        applies inside row schema *validation*, not to the diagnostic field
        itself."""
        ds = _make(row_schema={"id": "int64", "name": "string"})
        ds.read()

        assert ds.operation.schema == {"id": "int64[pyarrow]", "name": "string[pyarrow]"}
        assert ds.operation.schema != ds.row_schema

    def test_docstring_example_row_schema_is_valid(self):
        """Guards against the docstring example drifting from a value that
        actually normalizes and validates correctly."""

        @dataclass(kw_only=True)
        class _WithTimestamp(_RowSchemaDataset):
            def read(self) -> None:
                self.output = pd.DataFrame(
                    {
                        "id": [1, 2, 3],
                        "name": ["a", "b", "c"],
                        "created_at": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
                    }
                )

        ds = _WithTimestamp(
            id=uuid.uuid4(),
            name="with-ts",
            version="1.0.0",
            settings=_DummyDatasetSettings(),
            linked_service=_DummyLinkedService(
                id=uuid.uuid4(),
                name="ls",
                version="1.0.0",
                settings=_DummyLinkedServiceSettings(),
            ),
            row_schema={"id": "int64", "name": "string", "created_at": "timestamp"},
        )
        ds.read()  # must not raise

        assert ds.operation.success is True

    def test_convert_dtypes_not_called_twice(self, monkeypatch):
        """``_validate_output_row_schema`` must reuse ``self.operation.schema``
        instead of re-running ``convert_dtypes`` a second time."""
        call_count = 0
        original = pd.DataFrame.convert_dtypes

        def _counting_convert_dtypes(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            return original(self, *args, **kwargs)

        monkeypatch.setattr(pd.DataFrame, "convert_dtypes", _counting_convert_dtypes)

        ds = _make(row_schema={"id": "int64", "name": "string"})
        ds.read()

        assert call_count == 1


class TestNoOpStaleOutputExemption:
    """Empty-input no-ops on create/update/upsert/delete must never be
    rejected because of stale self.output from a previous call."""

    def test_empty_input_create_after_list_does_not_raise(self):
        """Reproduces: list() leaves a `{"resource": [...]}`-shaped
        self.output; a subsequent empty-input create() is a contract-
        guaranteed no-op and must not be row-schema-validated against it."""
        ds = _make(row_schema={"id": "int64", "name": "string"})
        ds.list()
        assert ds.operation.success is True

        ds.input = pd.DataFrame()  # empty input => no-op per contract
        ds.create()  # must not raise RowSchemaValidationError

        assert ds.operation.success is True

    def test_none_input_is_treated_as_empty(self):
        ds = _make(row_schema={"id": "int64", "name": "string"})
        ds.list()

        ds.input = None
        ds.create()

        assert ds.operation.success is True

    @pytest.mark.parametrize("method_name", ["create", "update", "upsert", "delete"])
    def test_empty_input_skips_validation_for_all_write_methods(self, method_name):
        ds = _make(row_schema={"id": "int64", "name": "string"})
        ds.list()  # stale, mismatched self.output

        ds.input = pd.DataFrame()
        getattr(ds, method_name)()

        assert ds.operation.success is True

    def test_read_is_not_exempted_by_empty_input(self):
        """`read()` does not consume `self.input`, so the no-op exemption
        must not apply to it -- an empty *result* still gets the ordinary
        empty-output skip (separate rule), but a non-empty mismatched result
        must still raise."""
        ds = _make(row_schema={"id": "int64", "email": "string"})

        with pytest.raises(RowSchemaValidationError):
            ds.read()


class TestPartialRowSchemaMatchForWrites:
    """create/update/upsert/delete may legitimately emit
    self.output = self.input.copy() with only a subset of the declared
    row schema -- not the full row -- when the backend has no
    RETURNING-style response."""

    @pytest.mark.parametrize("method_name", ["create", "update", "upsert", "delete"])
    def test_partial_columns_pass(self, method_name):
        """Reproduces: a contract-compliant partial write (only an identity
        column) must not be rejected for lacking the full row schema."""
        ds = _make(row_schema={"id": "int64", "name": "string", "email": "string"})
        ds.input = pd.DataFrame({"id": [1, 2]})  # identity column only

        getattr(ds, method_name)()  # must not raise

        assert ds.operation.success is True

    def test_create_with_server_assigned_autoincrement_id_passes(self):
        """Reproduces: a row schema with a server-assigned autoincrement
        `id` plus a no-RETURNING backend means self.input/self.output
        never carries `id` -- a fully contract-compliant create() must not
        fail."""
        ds = _make(row_schema={"id": "int64", "name": "string"})
        ds.input = pd.DataFrame({"name": ["Alice", "Bob"]})  # caller never supplies "id"

        ds.create()  # must not raise RowSchemaValidationError

        assert ds.operation.success is True

    @pytest.mark.parametrize("method_name", ["create", "update", "upsert", "delete"])
    def test_present_column_type_mismatch_still_raises(self, method_name):
        ds = _make(row_schema={"id": "string", "name": "string"})
        ds.input = pd.DataFrame({"id": [1, 2]})  # declared as string, actually int

        with pytest.raises(RowSchemaValidationError) as exc_info:
            getattr(ds, method_name)()

        assert "id" in exc_info.value.details["mismatched"]

    @pytest.mark.parametrize("method_name", ["create", "update", "upsert", "delete"])
    def test_undeclared_column_still_raises(self, method_name):
        ds = _make(row_schema={"id": "int64"})
        ds.input = pd.DataFrame({"id": [1], "undeclared": ["x"]})

        with pytest.raises(RowSchemaValidationError) as exc_info:
            getattr(ds, method_name)()

        assert "undeclared" in exc_info.value.details["unknown"]

    def test_read_still_requires_full_row_schema(self):
        """`read()` is the only method left in the exact-match set -- it has
        no `self.output = self.input.copy()` fallback, so it always returns
        the real backend result set and must satisfy the full row schema."""
        ds = _make(row_schema={"id": "int64", "name": "string", "missing_col": "string"})

        with pytest.raises(RowSchemaValidationError):
            ds.read()
