"""
File: test_yaml_parsing.py
Description: Test YAML parsing and resource loading
Region: packages/shared
"""

from unittest.mock import Mock, patch

import yaml

from ds_resource_plugin_py_lib.common.resource.client import ResourceClient


class TestYAMLParsing:
    """Test YAML parsing and resource loading."""

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_load_resource_yaml(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml):
        """Test loading and parsing of valid resource.yaml files."""
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
        assert client.resources["graphql"]["name"] == "graphql"
        assert client.resources["graphql"]["description"] == "GraphQL provider for the DS Business Workflow"

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_resource_yaml_missing(self, mock_import_module, mock_entry_points, temp_dir):
        """Test handling when resource.yaml doesn't exist."""
        # Setup
        ep = Mock()
        ep.name = "test"
        ep.module = "test_module"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        # Execute
        client = ResourceClient()

        # Assert
        assert len(client.resources) == 0

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_resource_yaml_empty(self, mock_import_module, mock_entry_points, temp_dir):
        """Test handling of empty resource.yaml files."""
        # Setup
        ep = Mock()
        ep.name = "test"
        ep.module = "test_module"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        resource_file = temp_dir / "resource.yaml"
        resource_file.write_text("")

        # Execute
        client = ResourceClient()

        # Assert
        assert len(client.resources) == 0

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_resource_yaml_invalid(self, mock_import_module, mock_entry_points, temp_dir):
        """Test handling of invalid YAML syntax."""
        # Setup
        ep = Mock()
        ep.name = "test"
        ep.module = "test_module"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        resource_file = temp_dir / "resource.yaml"
        resource_file.write_text("invalid: yaml: content: [unclosed")

        # Execute
        client = ResourceClient()

        # Assert
        assert len(client.resources) == 0

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_parse_linked_services(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml):
        """Test parsing of linked services from resource config."""
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
        assert ("DS.RESOURCE.LINKED_SERVICE.GRAPHQL", "1.0.0") in client.linked_services
        linked_service = client.linked_services[("DS.RESOURCE.LINKED_SERVICE.GRAPHQL", "1.0.0")]
        assert linked_service.kind == "DS.RESOURCE.LINKED_SERVICE.GRAPHQL"
        assert linked_service.name == "GRAPHQL"
        assert linked_service.version == "1.0.0"
        assert linked_service.class_name == "ds_protocol_graphql_py_lib.linked_service.graphql.GraphQLLinkedService"

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_parse_datasets(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml):
        """Test parsing of datasets from resource config."""
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
        assert ("DS.RESOURCE.DATASET.GRAPHQL", "1.0.0") in client.datasets
        dataset = client.datasets[("DS.RESOURCE.DATASET.GRAPHQL", "1.0.0")]
        assert dataset.kind == "DS.RESOURCE.DATASET.GRAPHQL"
        assert dataset.name == "GRAPHQL"
        assert dataset.version == "1.0.0"
        assert dataset.class_name == "ds_protocol_graphql_py_lib.dataset.graphql.GraphQLDataset"

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_multiple_resources(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml, http_resource_yaml):
        """Test discovery of multiple resources with same/different names."""
        # Setup
        ep1 = Mock()
        ep1.name = "graphql"
        ep1.module = "ds_protocol_graphql_py_lib"

        ep2 = Mock()
        ep2.name = "http"
        ep2.module = "ds_protocol_http_py_lib"

        mock_entry_points.return_value = [ep1, ep2]

        graphql_dir = temp_dir / "graphql"
        graphql_dir.mkdir()
        http_dir = temp_dir / "http"
        http_dir.mkdir()

        def import_module_side_effect(module_name):
            module = Mock()
            if module_name == "ds_protocol_graphql_py_lib":
                module.__file__ = str(graphql_dir / "__init__.py")
            elif module_name == "ds_protocol_http_py_lib":
                module.__file__ = str(http_dir / "__init__.py")
            return module

        mock_import_module.side_effect = import_module_side_effect

        with (graphql_dir / "resource.yaml").open("w") as f:
            yaml.dump(graphql_resource_yaml, f)
        with (http_dir / "resource.yaml").open("w") as f:
            yaml.dump(http_resource_yaml, f)

        # Execute
        client = ResourceClient()

        # Assert
        assert "graphql" in client.resources
        assert "http" in client.resources
        assert len(client.resources) == 2
