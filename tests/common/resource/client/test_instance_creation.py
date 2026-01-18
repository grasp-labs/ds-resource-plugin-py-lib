"""
**File:** ``test_instance_creation.py``
**Region:** ``tests/common/resource/client``

Description
-----------
Test instance creation from config dictionaries.
"""

from unittest.mock import Mock, patch

import pytest
import yaml
from ds_common_serde_py_lib.errors import DeserializationError

from ds_resource_plugin_py_lib.common.resource.client import ResourceClient


class TestInstanceCreation:
    """Test instance creation from config dictionaries."""

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_string")
    def test_linked_service_creation(
        self,
        mock_import_string,
        mock_import_module,
        mock_entry_points,
        temp_dir,
        graphql_resource_yaml,
        mock_linked_service_class,
    ):
        """Test creating linked service instance from config dict."""
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

        mock_import_string.return_value = mock_linked_service_class

        client = ResourceClient()

        config = {
            "kind": "DS.RESOURCE.LINKED_SERVICE.GRAPHQL",
            "version": "1.0.0",
            "settings": {"url": "https://example.com/graphql"},
        }

        # Execute
        linked_service = client.linked_service(config)

        # Assert
        assert linked_service is not None
        mock_linked_service_class.deserialize.assert_called_once_with(config)

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_string")
    def test_dataset_creation(
        self,
        mock_import_string,
        mock_import_module,
        mock_entry_points,
        temp_dir,
        graphql_resource_yaml,
        mock_dataset_class,
    ):
        """Test creating dataset instance from config dict."""
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

        mock_import_string.return_value = mock_dataset_class

        client = ResourceClient()

        config = {
            "kind": "DS.RESOURCE.DATASET.GRAPHQL",
            "version": "1.0.0",
            "settings": {"query": "query { users { id } }"},
        }

        # Execute
        dataset = client.dataset(config)

        # Assert
        assert dataset is not None
        mock_dataset_class.deserialize.assert_called_once_with(config)

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    def test_linked_service_missing_kind(self, mock_entry_points):
        """Test error handling when kind is missing."""
        # Setup
        mock_entry_points.return_value = []
        client = ResourceClient()

        config = {"version": "1.0.0", "settings": {"url": "https://example.com"}}

        # Execute & Assert
        with pytest.raises(DeserializationError) as exc_info:
            client.linked_service(config)
        assert "kind" in str(exc_info.value.details.get("error", ""))

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    def test_dataset_missing_kind(self, mock_entry_points):
        """Test error handling when kind is missing."""
        # Setup
        mock_entry_points.return_value = []
        client = ResourceClient()

        config = {"version": "1.0.0", "settings": {"query": "query { users }"}}

        # Execute & Assert
        with pytest.raises(DeserializationError) as exc_info:
            client.dataset(config)
        assert "kind" in str(exc_info.value.details.get("error", ""))

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    def test_linked_service_unknown_kind(self, mock_entry_points):
        """Test error handling when kind is not found."""
        # Setup
        mock_entry_points.return_value = []
        client = ResourceClient()

        config = {"kind": "DS.RESOURCE.LINKED_SERVICE.UNKNOWN", "version": "1.0.0"}

        # Execute & Assert
        with pytest.raises(DeserializationError):
            client.linked_service(config)

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    def test_dataset_unknown_kind(self, mock_entry_points):
        """Test error handling when kind is not found."""
        # Setup
        mock_entry_points.return_value = []
        client = ResourceClient()

        config = {"kind": "DS.RESOURCE.DATASET.UNKNOWN", "version": "1.0.0"}

        # Execute & Assert
        with pytest.raises(DeserializationError):
            client.dataset(config)

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_string")
    def test_linked_service_deserialization_error(
        self,
        mock_import_string,
        mock_import_module,
        mock_entry_points,
        temp_dir,
        graphql_resource_yaml,
        mock_linked_service_class,
    ):
        """Test DeserializationError on deserialize failure."""
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

        mock_import_string.return_value = mock_linked_service_class
        mock_linked_service_class.deserialize.side_effect = TypeError("Invalid config")

        client = ResourceClient()

        config = {
            "kind": "DS.RESOURCE.LINKED_SERVICE.GRAPHQL",
            "version": "1.0.0",
            "settings": {"invalid": "data"},
        }

        # Execute & Assert
        with pytest.raises(DeserializationError) as exc_info:
            client.linked_service(config)

        assert "Error deserializing linked service" in str(exc_info.value.message)

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_string")
    def test_dataset_deserialization_error(
        self,
        mock_import_string,
        mock_import_module,
        mock_entry_points,
        temp_dir,
        graphql_resource_yaml,
        mock_dataset_class,
    ):
        """Test DeserializationError on deserialize failure."""
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

        mock_import_string.return_value = mock_dataset_class
        mock_dataset_class.deserialize.side_effect = TypeError("Invalid config")

        client = ResourceClient()

        config = {
            "kind": "DS.RESOURCE.DATASET.GRAPHQL",
            "version": "1.0.0",
            "settings": {"invalid": "data"},
        }

        # Execute & Assert
        with pytest.raises(DeserializationError) as exc_info:
            client.dataset(config)

        assert "Error deserializing dataset" in str(exc_info.value.message)
