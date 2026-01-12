"""
**File:** ``test_base_serializer.py``
**Region:** ``tests/common/serde/serialize``

Description
-----------
Cover `DataSerializer` base class behavior.
"""

import pytest

from ds_resource_plugin_py_lib.common.serde.serialize.base import DataSerializer


def test_data_serializer_call_is_not_implemented():
    """Test that the DataSerializer call is not implemented."""
    serializer = DataSerializer()
    with pytest.raises(NotImplementedError):
        serializer({"any": "object"})
