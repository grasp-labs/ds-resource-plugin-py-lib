"""
**File:** ``test_discovery.py``
**Region:** ``tests/common/resource/client``

Description
-----------
Test resource discovery via entry points.
"""

from unittest.mock import Mock, patch

import yaml

from ds_resource_plugin_py_lib.common.resource.client import ResourceClient


class TestResourceDiscovery:
    """Test resource discovery via entry points."""

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_discover_protocols(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml):
        """Test discovery of resources from ds.protocols entry point group."""
        # Setup
        ep = Mock()
        ep.name = "graphql"
        ep.module = "ds_protocol_graphql_py_lib"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        resource_file = temp_dir / "resource.yaml"
        with resource_file.open("w") as f:
            yaml.dump(graphql_resource_yaml, f)

        # Execute
        client = ResourceClient()

        # Assert
        assert "graphql" in client.resources
        assert len(client.resources) == 1
        mock_entry_points.assert_any_call(group="ds.protocols")

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_discover_providers(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml):
        """Test discovery of resources from ds.providers entry point group."""
        # Setup
        ep = Mock()
        ep.name = "graphql"
        ep.module = "ds_protocol_graphql_py_lib"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        resource_file = temp_dir / "resource.yaml"
        with resource_file.open("w") as f:
            yaml.dump(graphql_resource_yaml, f)

        # Execute
        client = ResourceClient()

        # Assert
        assert "graphql" in client.resources
        mock_entry_points.assert_any_call(group="ds.providers")

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_discover_both_groups(
        self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml, http_resource_yaml
    ):
        """Test that both protocol and provider groups are discovered."""
        # Setup
        protocol_ep = Mock()
        protocol_ep.name = "graphql"
        protocol_ep.module = "ds_protocol_graphql_py_lib"

        provider_ep = Mock()
        provider_ep.name = "http"
        provider_ep.module = "ds_protocol_http_py_lib"

        def entry_points_side_effect(group):
            if group == "ds.protocols":
                return [protocol_ep]
            elif group == "ds.providers":
                return [provider_ep]
            return []

        mock_entry_points.side_effect = entry_points_side_effect

        protocol_dir = temp_dir / "graphql"
        protocol_dir.mkdir()
        http_dir = temp_dir / "http"
        http_dir.mkdir()

        def import_module_side_effect(module_name):
            module = Mock()
            if module_name == "ds_protocol_graphql_py_lib":
                module.__file__ = str(protocol_dir / "__init__.py")
            elif module_name == "ds_protocol_http_py_lib":
                module.__file__ = str(http_dir / "__init__.py")
            return module

        mock_import_module.side_effect = import_module_side_effect

        with (protocol_dir / "resource.yaml").open("w") as f:
            yaml.dump(graphql_resource_yaml, f)
        with (http_dir / "resource.yaml").open("w") as f:
            yaml.dump(http_resource_yaml, f)

        # Execute
        client = ResourceClient()

        # Assert
        assert "graphql" in client.resources
        assert "http" in client.resources
        assert len(client.resources) == 2

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    def test_entry_points_exception(self, mock_entry_points):
        """Test graceful handling when entry_points() raises exception."""
        # Setup
        mock_entry_points.side_effect = Exception("Entry point error")

        # Execute
        client = ResourceClient()

        # Assert
        assert len(client.resources) == 0

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_entry_point_no_file(self, mock_import_module, mock_entry_points):
        """Test handling of entry points without __file__ attribute."""
        # Setup
        ep = Mock()
        ep.name = "test"
        ep.module = "test_module"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = None
        mock_import_module.return_value = module

        # Execute
        client = ResourceClient()

        # Assert
        assert len(client.resources) == 0

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_entry_point_import_error(self, mock_import_module, mock_entry_points):
        """Test handling of import errors for entry point modules."""
        # Setup
        ep = Mock()
        ep.name = "test"
        ep.module = "test_module"
        mock_entry_points.return_value = [ep]

        mock_import_module.side_effect = ImportError("Cannot import module")

        # Execute
        client = ResourceClient()

        # Assert
        assert len(client.resources) == 0
