"""
**File:** ``test_version_differentiation.py``
**Region:** ``tests/common/resource/client``

Description
-----------
Test version differentiation for datasets.
"""

from unittest.mock import Mock, patch

import pytest
import yaml
from ds_common_serde_py_lib.errors import DeserializationError

from ds_resource_plugin_py_lib.common.resource.client import ResourceClient
from ds_resource_plugin_py_lib.common.resource.dataset.base import DatasetInfo


class TestVersionDifferentiation:
    """Test version differentiation for datasets."""

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_multiple_dataset_versions(self, mock_import_module, mock_entry_points, temp_dir, http_resource_yaml):
        """Test parsing resource.yaml with multiple dataset versions (same kind, different versions)."""
        # Setup
        ep = Mock()
        ep.name = "http"
        ep.module = "ds_protocol_http_py_lib"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        resource_file = temp_dir / "resource.yaml"
        with resource_file.open("w") as f:
            yaml.dump(http_resource_yaml, f)

        # Execute
        client = ResourceClient()

        # Assert
        # Both versions should be stored with composite keys (kind, version)
        assert ("DS.RESOURCE.DATASET.HTTP", "1.0.0") in client.datasets
        assert ("DS.RESOURCE.DATASET.HTTP", "2.0.0") in client.datasets

        # Verify v1.0.0
        dataset_info_v1 = client.datasets[("DS.RESOURCE.DATASET.HTTP", "1.0.0")]
        assert dataset_info_v1.version == "1.0.0"
        assert dataset_info_v1.class_name == "ds_protocol_http_py_lib.dataset.http.HttpDataset"

        # Verify v2.0.0
        dataset_info_v2 = client.datasets[("DS.RESOURCE.DATASET.HTTP", "2.0.0")]
        assert dataset_info_v2.version == "2.0.0"
        assert dataset_info_v2.class_name == "ds_protocol_http_py_lib.dataset.httpV2.HttpDataset"

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_version_in_dataset_info(self, mock_import_module, mock_entry_points, temp_dir, http_resource_yaml):
        """Test that DatasetInfo correctly stores version information."""
        # Setup
        ep = Mock()
        ep.name = "http"
        ep.module = "ds_protocol_http_py_lib"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        resource_file = temp_dir / "resource.yaml"
        with resource_file.open("w") as f:
            yaml.dump(http_resource_yaml, f)

        # Execute
        client = ResourceClient()

        # Assert
        # Both versions should be stored
        assert ("DS.RESOURCE.DATASET.HTTP", "1.0.0") in client.datasets
        assert ("DS.RESOURCE.DATASET.HTTP", "2.0.0") in client.datasets

        dataset_info_v1 = client.datasets[("DS.RESOURCE.DATASET.HTTP", "1.0.0")]
        assert isinstance(dataset_info_v1, DatasetInfo)
        assert dataset_info_v1.version == "1.0.0"

        dataset_info_v2 = client.datasets[("DS.RESOURCE.DATASET.HTTP", "2.0.0")]
        assert isinstance(dataset_info_v2, DatasetInfo)
        assert dataset_info_v2.version == "2.0.0"

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_both_versions_stored(self, mock_import_module, mock_entry_points, temp_dir, http_resource_yaml):
        """Test that when multiple versions share same kind, both are stored with composite keys."""
        # Setup
        ep = Mock()
        ep.name = "http"
        ep.module = "ds_protocol_http_py_lib"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        resource_file = temp_dir / "resource.yaml"
        with resource_file.open("w") as f:
            yaml.dump(http_resource_yaml, f)

        # Execute
        client = ResourceClient()

        # Assert
        # Both versions should be stored separately
        assert ("DS.RESOURCE.DATASET.HTTP", "1.0.0") in client.datasets
        assert ("DS.RESOURCE.DATASET.HTTP", "2.0.0") in client.datasets

        dataset_info_v1 = client.datasets[("DS.RESOURCE.DATASET.HTTP", "1.0.0")]
        assert dataset_info_v1.version == "1.0.0"
        assert "http" in dataset_info_v1.class_name
        assert "httpV2" not in dataset_info_v1.class_name

        dataset_info_v2 = client.datasets[("DS.RESOURCE.DATASET.HTTP", "2.0.0")]
        assert dataset_info_v2.version == "2.0.0"
        assert "httpV2" in dataset_info_v2.class_name

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_string")
    def test_dataset_version_selection_with_version(
        self,
        mock_import_string,
        mock_import_module,
        mock_entry_points,
        temp_dir,
        http_resource_yaml,
        mock_dataset_class,
    ):
        """Test creating dataset instance with specific version - should use that version."""
        # Setup
        ep = Mock()
        ep.name = "http"
        ep.module = "ds_protocol_http_py_lib"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        resource_file = temp_dir / "resource.yaml"
        with resource_file.open("w") as f:
            yaml.dump(http_resource_yaml, f)

        mock_import_string.return_value = mock_dataset_class

        client = ResourceClient()

        # Config specifies version 1.0.0, so it should use that version
        config = {
            "kind": "DS.RESOURCE.DATASET.HTTP",
            "version": "1.0.0",
            "typed_properties": {"url": "https://example.com"},
        }

        # Execute
        dataset = client.dataset(config)

        # Assert
        assert dataset is not None
        # Verify that import_string was called with v1 class name
        mock_import_string.assert_called_with("ds_protocol_http_py_lib.dataset.http.HttpDataset")
        mock_dataset_class.deserialize.assert_called_once_with(config)

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_dataset_missing_version(
        self,
        mock_import_module,
        mock_entry_points,
        temp_dir,
        http_resource_yaml,
    ):
        """Test error handling when version is missing from config."""
        # Setup
        ep = Mock()
        ep.name = "http"
        ep.module = "ds_protocol_http_py_lib"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        resource_file = temp_dir / "resource.yaml"
        with resource_file.open("w") as f:
            yaml.dump(http_resource_yaml, f)

        client = ResourceClient()
        config = {
            "kind": "DS.RESOURCE.DATASET.HTTP",
            "typed_properties": {"url": "https://example.com"},
        }

        with pytest.raises(DeserializationError) as exc_info:
            client.dataset(config)
        assert "version" in str(exc_info.value.details.get("error", ""))
