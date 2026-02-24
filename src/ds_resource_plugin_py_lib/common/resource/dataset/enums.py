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
