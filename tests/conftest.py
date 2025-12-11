"""
File: conftest.py
Description: Shared pytest fixtures for resource client tests
Region: packages/shared
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from ds_resource_plugin_py_lib.common.resource.dataset.base import Dataset
from ds_resource_plugin_py_lib.common.resource.linked_service.base import LinkedService


@pytest.fixture
def temp_dir():
    """Create a temporary directory for resource.yaml files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def graphql_resource_yaml():
    """GraphQL resource.yaml content."""
    return {
        "package-name": "graphql",
        "name": "graphql",
        "description": "GraphQL provider for the DS Business Workflow",
        "dataset": [
            {
                "name": "GRAPHQL",
                "kind": "DS.RESOURCE.DATASET.GRAPHQL",
                "version": "1.0.0",
                "description": "GRAPHQL dataset",
                "class_name": "ds_protocol_graphql_py_lib.dataset.graphql.GraphQLDataset",
            }
        ],
        "linked_service": [
            {
                "name": "GRAPHQL",
                "kind": "DS.RESOURCE.LINKED_SERVICE.GRAPHQL",
                "version": "1.0.0",
                "description": "GRAPHQL linked service",
                "class_name": "ds_protocol_graphql_py_lib.linked_service.graphql.GraphQLLinkedService",
            }
        ],
    }


@pytest.fixture
def http_resource_yaml():
    """HTTP resource.yaml content with multiple dataset versions."""
    return {
        "package-name": "http",
        "name": "http",
        "description": "HTTP protocol for the DS Business Workflow",
        "dataset": [
            {
                "name": "HTTP",
                "kind": "DS.RESOURCE.DATASET.HTTP",
                "version": "1.0.0",
                "description": "HTTP dataset",
                "class_name": "ds_protocol_http_py_lib.dataset.http.HttpDataset",
            },
            {
                "name": "HTTP",
                "kind": "DS.RESOURCE.DATASET.HTTP",
                "version": "2.0.0",
                "description": "HTTP dataset",
                "class_name": "ds_protocol_http_py_lib.dataset.httpV2.HttpDataset",
            },
        ],
        "linked_service": [
            {
                "name": "HTTP",
                "kind": "DS.RESOURCE.LINKED_SERVICE.HTTP",
                "version": "1.0.0",
                "description": "HTTP linked service",
                "class_name": "ds_protocol_http_py_lib.linked_service.http.HttpLinkedService",
            }
        ],
    }


@pytest.fixture
def mock_entry_point():
    """Create a mock entry point."""
    ep = Mock()
    ep.name = "test_protocol"
    ep.module = "test_module"
    ep.value = "test_module:TestClass"
    return ep


@pytest.fixture
def mock_module(temp_dir):
    """Create a mock module with __file__ pointing to temp directory."""
    module = Mock()
    module.__file__ = str(temp_dir / "__init__.py")
    return module


@pytest.fixture
def mock_dataset_class():
    """Create a mock Dataset class with deserialize method."""
    mock_cls = Mock(spec=Dataset)
    mock_instance = Mock(spec=Dataset)
    mock_cls.deserialize = Mock(return_value=mock_instance)
    return mock_cls


@pytest.fixture
def mock_linked_service_class():
    """Create a mock LinkedService class with deserialize method."""
    mock_cls = Mock(spec=LinkedService)
    mock_instance = Mock(spec=LinkedService)
    mock_cls.deserialize = Mock(return_value=mock_instance)
    return mock_cls


def create_resource_yaml_file(temp_dir, yaml_content):
    """Helper function to create a resource.yaml file in temporary directory."""
    resource_file = temp_dir / "resource.yaml"
    with resource_file.open("w") as f:
        yaml.dump(yaml_content, f)
    return temp_dir
