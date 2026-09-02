"""
**File:** ``dataset_row_schema_example.py``
**Region:** ``examples``

Description
-----------
Runnable example showing how to declare and enforce ``TabularDataset.row_schema``.

This mimics a simple key-value "table" provider (think: an in-memory stand-in
for a Postgres/SQLite table) that supports ``read()`` and ``update()``. It
demonstrates:

1. Declaring a row schema on dataset construction.
2. A successful ``read()`` where the source output matches the row schema.
3. A contract-compliant ``update()`` that only returns identity/changed
   columns (partial-match row schema validation).
4. A row schema violation on ``read()`` raising ``RowSchemaValidationError``.

Run directly:

    uv run python examples/dataset_row_schema_example.py
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import pandas as pd

from ds_resource_plugin_py_lib.common.resource.dataset.base import (
    DatasetSettings,
    TabularDataset,
)
from ds_resource_plugin_py_lib.common.resource.dataset.errors import RowSchemaValidationError
from ds_resource_plugin_py_lib.common.resource.linked_service.base import (
    LinkedService,
    LinkedServiceSettings,
)
from ds_resource_plugin_py_lib.common.serde.deserialize.base import DataDeserializer
from ds_resource_plugin_py_lib.common.serde.serialize.base import DataSerializer


# --------------------------------------------------------------------------
# A trivial in-memory "backend" standing in for a real database/API.
# --------------------------------------------------------------------------
_BACKEND_TABLE = pd.DataFrame(
    {
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Carol"],
        "email": ["alice@example.com", "bob@example.com", "carol@example.com"],
    }
)


@dataclass(kw_only=True)
class InMemoryLinkedServiceSettings(LinkedServiceSettings):
    """Nothing to configure -- the backend is an in-process DataFrame."""


@dataclass(kw_only=True)
class InMemoryLinkedService(LinkedService[InMemoryLinkedServiceSettings]):
    """A linked service standing in for a database connection."""

    settings: InMemoryLinkedServiceSettings

    @property
    def type(self):  # type: ignore[override]
        class _T(StrEnum):
            IN_MEMORY = "in_memory"

        return _T.IN_MEMORY

    @property
    def connection(self) -> Any:
        return _BACKEND_TABLE

    def connect(self) -> None:
        pass  # nothing to establish -- backend is already "in memory"

    def test_connection(self) -> tuple[bool, str]:
        return (True, "")

    def close(self) -> None:
        pass


@dataclass(kw_only=True)
class UsersDatasetSettings(DatasetSettings):
    """No provider-specific settings needed for this toy example."""


@dataclass(kw_only=True)
class UsersDataset(
    TabularDataset[InMemoryLinkedService, UsersDatasetSettings, DataSerializer, DataDeserializer]
):
    """A dataset representing the `users` table."""

    settings: UsersDatasetSettings
    linked_service: InMemoryLinkedService

    @property
    def type(self):  # type: ignore[override]
        class _T(StrEnum):
            USERS = "users"

        return _T.USERS

    def read(self) -> None:
        # Full result set -- must satisfy the full declared row schema.
        self.output = self.linked_service.connection.copy()

    def update(self) -> None:
        # No-op on empty input, per DATASET_CONTRACT.md.
        if self.input is None or len(self.input) == 0:
            return
        # Backend has no RETURNING-style response here, so per contract we
        # echo back exactly what the caller asked to update -- which may
        # legitimately be only the identity + changed columns, not every
        # column in the row schema.
        self.output = self.input.copy()

    def create(self) -> None:
        # No-op on empty input, per DATASET_CONTRACT.md.
        if self.input is None or len(self.input) == 0:
            return
        # Backend has no RETURNING-style response, so it echoes back exactly
        # what the caller supplied. "id" is a server-assigned autoincrement
        # column the caller never supplies -- a legitimate partial subset of
        # the declared row schema, not a row schema violation.
        self.output = self.input.copy()

    def upsert(self) -> None:
        raise NotImplementedError

    def delete(self) -> None:
        raise NotImplementedError

    def purge(self) -> None:
        raise NotImplementedError

    def list(self) -> None:
        raise NotImplementedError

    def rename(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        pass


def _make_dataset(row_schema: dict[str, str] | None) -> UsersDataset:
    return UsersDataset(
        id=uuid.uuid4(),
        name="users",
        version="1.0.0",
        settings=UsersDatasetSettings(),
        linked_service=InMemoryLinkedService(
            id=uuid.uuid4(),
            name="in-memory",
            version="1.0.0",
            settings=InMemoryLinkedServiceSettings(),
        ),
        row_schema=row_schema,
    )


def main() -> None:
    # Declared row schema uses plain, portable logical type names -- not
    # pandas/PyArrow internals like "int64[pyarrow]". The library normalizes
    # both this declaration and the actual backend dtypes internally before
    # comparing them.
    users_schema = {
        "id": "int64",
        "name": "string",
        "email": "string",
    }

    # --- 1. Successful read(): full row set matches the declared row schema ---
    ds = _make_dataset(row_schema=users_schema)
    ds.read()
    print("read() succeeded:")
    print(ds.output)
    print(f"operation.success={ds.operation.success} row_count={ds.operation.row_count}")
    print()

    # --- 2. Contract-compliant partial update(): identity column only ---
    ds.input = pd.DataFrame({"id": [1]})  # only the identity column, no RETURNING
    ds.update()
    print("update() succeeded with partial columns:")
    print(ds.output)
    print(f"operation.success={ds.operation.success}")
    print()

    # --- 3. Contract-compliant partial create(): no server-assigned "id" ---
    # The backend auto-assigns "id" and has no RETURNING-style response, so
    # self.output = self.input.copy() never carries "id" either -- a
    # legitimate partial subset of the declared row schema, not a violation.
    ds.input = pd.DataFrame({"name": ["Dave"]})
    ds.create()
    print("create() succeeded without the server-assigned id column:")
    print(ds.output)
    print(f"operation.success={ds.operation.success}")
    print()

    # --- 4. Row schema violation: source no longer matches the declared shape ---
    bad_schema = {
        "id": "int64",
        "name": "string",
        "phone": "string",  # backend never returns "phone"
    }
    ds_bad = _make_dataset(row_schema=bad_schema)
    try:
        ds_bad.read()
    except RowSchemaValidationError as exc:
        print("read() correctly rejected -- row schema mismatch:")
        print(f"  message: {exc.message}")
        print(f"  details: {exc.details}")
        print(f"  operation.success={ds_bad.operation.success}")


if __name__ == "__main__":
    main()
