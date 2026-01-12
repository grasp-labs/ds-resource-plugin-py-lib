"""
**File:** ``test_scan_resource_directory.py``
**Region:** ``tests/common/resource/client``

Description
-----------
Cover `_scan_resource_directory` behavior for non-existent paths.
"""

from unittest.mock import patch

from ds_resource_plugin_py_lib.common.resource.client import ResourceClient


class TestScanResourceDirectory:
    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    def test_scan_resource_directory_nonexistent_path_is_noop(self, mock_entry_points):
        """Non-existent resource directories should be ignored gracefully."""
        mock_entry_points.return_value = []
        client = ResourceClient()

        client._scan_resource_directory("/this/path/should/not/exist")

        assert client.resources == {}
