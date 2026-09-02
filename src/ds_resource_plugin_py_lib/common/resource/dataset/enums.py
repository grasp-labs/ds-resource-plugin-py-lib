"""
**File:** ``enums.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/dataset``

Description
-----------
Enumerations for dataset operations.
"""

from enum import StrEnum


class DatasetMethod(StrEnum):
    """Allowed dataset operation names."""

    CREATE = "create"
    """Insert rows into the target. Atomic. Not idempotent."""
    READ = "read"
    """Read all data from the source into ``self.output``. Idempotent."""
    UPDATE = "update"
    """Update existing rows matched by identity columns. Atomic. Idempotent."""
    UPSERT = "upsert"
    """Insert or update rows matched by identity columns. Atomic. Idempotent."""
    DELETE = "delete"
    """Remove specific rows matched by identity columns. Atomic. Idempotent."""
    PURGE = "purge"
    """Remove all content from the target. Atomic. Idempotent."""
    LIST = "list"
    """Discover available resources and populate ``self.output``. Idempotent."""
    RENAME = "rename"
    """Rename a resource in the backend. Atomic. Not idempotent."""

    @staticmethod
    def all_values() -> frozenset[str]:
        """Return all operation method values as a frozen set."""
        return frozenset(m.value for m in DatasetMethod)

    @staticmethod
    def row_schema_validated_values() -> frozenset[str]:
        """
        Methods whose ``self.output`` represents dataset rows and must be
        checked against a declared ``TabularDataset.row_schema`` when one is
        present. This is a table/row data contract, distinct from the
        provider-facing JSON Schema used to validate a dataset's
        construction payload before ``deserialize()`` (see
        ``DATASET_CONTRACT.md`` -- "Schema and Dataclass Alignment").

        ``list()`` is excluded -- it returns resource-discovery metadata,
        not rows matching the dataset's own row schema. ``purge()`` and
        ``rename()`` are excluded -- they do not populate ``self.output``.

        See ``full_row_schema_match_values()`` /
        ``partial_row_schema_match_values()`` for how each of these methods
        is checked, and ``input_dependent_values()`` for the no-op
        exemption.
        """
        return frozenset(
            {
                DatasetMethod.CREATE,
                DatasetMethod.READ,
                DatasetMethod.UPDATE,
                DatasetMethod.UPSERT,
                DatasetMethod.DELETE,
            }
        )

    @staticmethod
    def full_row_schema_match_values() -> frozenset[str]:
        """
        Methods whose ``self.output`` must match ``TabularDataset.row_schema``
        exactly -- every declared column present with the declared type, no
        extra columns.

        Only ``read()`` qualifies: it is the sole row-schema-validated
        method with no ``self.output = self.input.copy()`` fallback, so its
        output is always the real backend result set, never a
        caller-supplied (and possibly partial) echo of ``self.input``.
        """
        return frozenset({DatasetMethod.READ})

    @staticmethod
    def partial_row_schema_match_values() -> frozenset[str]:
        """
        Methods whose ``self.output`` may legitimately contain only a subset
        of ``TabularDataset.row_schema``'s columns.

        Per ``DATASET_CONTRACT.md`` ("self.output after each method"), when a
        backend has no ``RETURNING``-style response, ``create()``/``update()``/
        ``upsert()``/``delete()`` may all set ``self.output = self.input.copy()``
        -- and ``self.input`` for those methods can legitimately omit columns
        the backend fills in itself (e.g. a server-assigned autoincrement
        ``id``, or identity/changed-only columns for update/upsert/delete).
        Present columns are still checked against ``row_schema``; declared
        columns missing from the output are not an error for these methods.
        """
        return frozenset(
            {
                DatasetMethod.CREATE,
                DatasetMethod.UPDATE,
                DatasetMethod.UPSERT,
                DatasetMethod.DELETE,
            }
        )

    @staticmethod
    def input_dependent_values() -> frozenset[str]:
        """
        Methods that use ``self.input`` (``DATASET_CONTRACT.md`` -- "Input
        Handling"). Per contract, these must no-op silently -- without
        touching the backend or raising -- when ``self.input`` is ``None`` or
        empty. ``self.output`` is not required to be reset on a no-op and may
        still hold a previous call's data, so row schema validation must not
        run against it in that case.
        """
        return frozenset(
            {
                DatasetMethod.CREATE,
                DatasetMethod.UPDATE,
                DatasetMethod.UPSERT,
                DatasetMethod.DELETE,
            }
        )
