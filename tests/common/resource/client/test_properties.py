"""
**File:** ``test_properties.py``
**Region:** ``tests/common/resource/client``

Description
-----------
Test properties and internal state.
"""

from unittest.mock import Mock, patch

import yaml

from ds_resource_plugin_py_lib.common.resource.client import ResourceClient
from ds_resource_plugin_py_lib.common.resource.dataset.base import DatasetInfo
from ds_resource_plugin_py_lib.common.resource.linked_service.base import LinkedServiceInfo


class TestPropertiesAndState:
    """Test properties and internal state."""

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_resources_property(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml):
        """Test that resources property returns correct dictionary."""
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
        resources = client.resources
        assert isinstance(resources, dict)
        assert "graphql" in resources
        assert resources["graphql"]["name"] == "graphql"

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_linked_services_property(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml):
        """Test that linked_services property returns correct dictionary keyed by (type, version)."""
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
        linked_services = client.linked_services
        assert isinstance(linked_services, dict)
        assert ("DS.RESOURCE.LINKED_SERVICE.GRAPHQL", "1.0.0") in linked_services
        assert isinstance(linked_services[("DS.RESOURCE.LINKED_SERVICE.GRAPHQL", "1.0.0")], LinkedServiceInfo)

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_datasets_property(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml):
        """Test that datasets property returns correct dictionary keyed by (type, version)."""
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
        datasets = client.datasets
        assert isinstance(datasets, dict)
        assert ("DS.RESOURCE.DATASET.GRAPHQL", "1.0.0") in datasets
        assert isinstance(datasets[("DS.RESOURCE.DATASET.GRAPHQL", "1.0.0")], DatasetInfo)

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_resource_dict_structure(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml):
        """Test that resource_dict contains expected structure."""
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
        resource = client.resources["graphql"]
        assert "name" in resource
        assert "description" in resource
        assert "dataset" in resource
        assert "linked_service" in resource
        assert len(resource["dataset"]) == 1
        assert len(resource["linked_service"]) == 1
