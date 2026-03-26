"""
**File:** ``test_serde_registration.py``
**Region:** ``tests/common/resource/client``

Description
-----------
Dedicated tests for serializer registration in ResourceClient.
"""

from copy import deepcopy
from unittest.mock import Mock, patch

import yaml

from ds_resource_plugin_py_lib.common.resource.client import ResourceClient
from ds_resource_plugin_py_lib.common.serde.serialize import (
    AWSWRANGLER_DATAFRAME_SERIALIZER_INFO,
    PANDAS_DATAFRAME_SERIALIZER_INFO,
)
from ds_resource_plugin_py_lib.common.serde.serialize.base import SerializerInfo


class TestSerdeRegistration:
    """Test serializer registration and version-aware storage."""

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    def test_builtin_serializers_registered(self, mock_entry_points):
        """Built-in dataframe serializers should be available without resource.yaml discovery."""
        mock_entry_points.return_value = []

        client = ResourceClient()

        pandas_serializer = client.serializers[PANDAS_DATAFRAME_SERIALIZER_INFO.key]
        awswrangler_serializer = client.serializers[AWSWRANGLER_DATAFRAME_SERIALIZER_INFO.key]

        assert isinstance(pandas_serializer, SerializerInfo)
        assert pandas_serializer == PANDAS_DATAFRAME_SERIALIZER_INFO
        assert awswrangler_serializer == AWSWRANGLER_DATAFRAME_SERIALIZER_INFO

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_parse_serializers(self, mock_import_module, mock_entry_points, temp_dir, graphql_resource_yaml):
        """Test parsing serializers from the top-level serde section."""
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

        client = ResourceClient()

        assert ("DS.RESOURCE.SERIALIZER.GRAPHQL_REQUEST", "1.0.0") in client.serializers
        serializer = client.serializers[("DS.RESOURCE.SERIALIZER.GRAPHQL_REQUEST", "1.0.0")]
        assert isinstance(serializer, SerializerInfo)
        assert serializer.type == "DS.RESOURCE.SERIALIZER.GRAPHQL_REQUEST"
        assert serializer.name == "GRAPHQL_REQUEST"
        assert serializer.version == "1.0.0"
        assert serializer.class_name == "ds_protocol_graphql_py_lib.serde.graphql.GraphQLRequestSerializer"

    @patch("ds_resource_plugin_py_lib.common.resource.client.entry_points")
    @patch("ds_resource_plugin_py_lib.common.resource.client.import_module")
    def test_multiple_serializer_versions(self, mock_import_module, mock_entry_points, temp_dir, http_resource_yaml):
        """Test serializers are stored by composite (type, version) key."""
        ep = Mock()
        ep.name = "http"
        ep.module = "ds_protocol_http_py_lib"
        mock_entry_points.return_value = [ep]

        module = Mock()
        module.__file__ = str(temp_dir / "__init__.py")
        mock_import_module.return_value = module

        resource_yaml = deepcopy(http_resource_yaml)
        resource_yaml["serde"].append(
            {
                "name": "HTTP_REQUEST",
                "type": "DS.RESOURCE.SERIALIZER.HTTP_REQUEST",
                "version": "2.0.0",
                "description": "HTTP request serializer v2",
                "class_name": "ds_protocol_http_py_lib.serde.http_v2.HttpRequestSerializer",
            }
        )

        resource_file = temp_dir / "resource.yaml"
        with resource_file.open("w") as f:
            yaml.dump(resource_yaml, f)

        client = ResourceClient()

        assert ("DS.RESOURCE.SERIALIZER.HTTP_REQUEST", "1.0.0") in client.serializers
        assert ("DS.RESOURCE.SERIALIZER.HTTP_REQUEST", "2.0.0") in client.serializers

        serializer_v1 = client.serializers[("DS.RESOURCE.SERIALIZER.HTTP_REQUEST", "1.0.0")]
        serializer_v2 = client.serializers[("DS.RESOURCE.SERIALIZER.HTTP_REQUEST", "2.0.0")]

        assert serializer_v1.class_name == "ds_protocol_http_py_lib.serde.http.HttpRequestSerializer"
        assert serializer_v2.class_name == "ds_protocol_http_py_lib.serde.http_v2.HttpRequestSerializer"
