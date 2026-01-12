"""
**File:** ``test_linked_service_info.py``
**Region:** ``tests/common/resource/linked_service``

Description
-----------
Tests for `LinkedServiceInfo` helpers.
"""

from ds_resource_plugin_py_lib.common.resource.linked_service.base import LinkedServiceInfo


def test_linked_service_info_str_and_key():
    """LinkedServiceInfo should expose human-readable str and composite key."""
    info = LinkedServiceInfo(
        kind="DS.RESOURCE.LINKED_SERVICE.EXAMPLE",
        name="example",
        class_name="module.Class",
        version="2.0.0",
        description="desc",
    )

    assert str(info) == "DS.RESOURCE.LINKED_SERVICE.EXAMPLE:v2.0.0"
    assert info.key == ("DS.RESOURCE.LINKED_SERVICE.EXAMPLE", "2.0.0")
