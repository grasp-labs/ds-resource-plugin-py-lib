"""
**File:** ``test_dataset_info.py``
**Region:** ``tests/common/resource/dataset``

Description
-----------
Tests for `DatasetInfo` helpers.
"""

from ds_resource_plugin_py_lib.common.resource.dataset.base import DatasetInfo


def test_dataset_info_str_and_key():
    """DatasetInfo should expose human-readable str and composite key."""
    info = DatasetInfo(
        type="DS.RESOURCE.DATASET.EXAMPLE",
        name="example",
        class_name="module.Class",
        version="1.2.3",
        description="desc",
    )

    assert str(info) == "DS.RESOURCE.DATASET.EXAMPLE:v1.2.3"
    assert info.key == ("DS.RESOURCE.DATASET.EXAMPLE", "1.2.3")
