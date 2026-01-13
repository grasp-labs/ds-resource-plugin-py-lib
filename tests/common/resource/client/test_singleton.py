"""
**File:** ``test_singleton.py``
**Region:** ``tests/common/resource/client``

Description
-----------
Test singleton pattern implementation.
"""

from unittest.mock import patch

from ds_resource_plugin_py_lib.common.resource.client import ResourceClient


class TestSingletonPattern:
    """Test singleton pattern implementation."""

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    def test_get_instance_singleton(self, mock_entry_points):
        """Test that get_instance() returns the same instance (using lru_cache)."""
        # Setup
        mock_entry_points.return_value = []

        # Execute
        instance1 = ResourceClient.get_instance()
        instance2 = ResourceClient.get_instance()

        # Assert
        assert instance1 is instance2

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    def test_get_instance_cached(self, mock_entry_points):
        """Test that multiple calls return cached instance."""
        # Setup
        mock_entry_points.return_value = []

        # Execute
        instance1 = ResourceClient.get_instance()
        instance2 = ResourceClient.get_instance()
        instance3 = ResourceClient.get_instance()

        # Assert
        assert instance1 is instance2 is instance3
