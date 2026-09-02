"""
**File:** ``test_dataset_method_enum.py``
**Region:** ``tests/common/resource/dataset``

Description
-----------
Cover ``DatasetMethod``'s classification helpers used to drive row schema
validation and the empty-input no-op exemption.
"""

from ds_resource_plugin_py_lib.common.resource.dataset.enums import DatasetMethod


def test_all_values():
    assert DatasetMethod.all_values() == {
        "create",
        "read",
        "update",
        "upsert",
        "delete",
        "purge",
        "list",
        "rename",
    }


def test_row_schema_validated_values():
    assert DatasetMethod.row_schema_validated_values() == {
        DatasetMethod.CREATE,
        DatasetMethod.READ,
        DatasetMethod.UPDATE,
        DatasetMethod.UPSERT,
        DatasetMethod.DELETE,
    }


def test_full_row_schema_match_values_is_read_only():
    """`read()` is the only row-schema-validated method with no
    `self.output = self.input.copy()` fallback."""
    assert DatasetMethod.full_row_schema_match_values() == {DatasetMethod.READ}


def test_partial_row_schema_match_values_covers_all_write_methods():
    """create/update/upsert/delete all share the no-RETURNING
    `self.output = self.input.copy()` fallback, so all four allow partial
    row schema matches."""
    assert DatasetMethod.partial_row_schema_match_values() == {
        DatasetMethod.CREATE,
        DatasetMethod.UPDATE,
        DatasetMethod.UPSERT,
        DatasetMethod.DELETE,
    }


def test_full_and_partial_match_sets_partition_row_schema_validated_values():
    """Every row-schema-validated method falls into exactly one match mode."""
    full = DatasetMethod.full_row_schema_match_values()
    partial = DatasetMethod.partial_row_schema_match_values()

    assert full | partial == DatasetMethod.row_schema_validated_values()
    assert full & partial == frozenset()


def test_input_dependent_values():
    assert DatasetMethod.input_dependent_values() == {
        DatasetMethod.CREATE,
        DatasetMethod.UPDATE,
        DatasetMethod.UPSERT,
        DatasetMethod.DELETE,
    }
