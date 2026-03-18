"""
**File:** ``client.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource``

Description
-----------
Resource client for discovering and managing datasets and linked services using entry points.

Example
-------
.. code-block:: python

    from ds_resource_plugin_py_lib.common.resource.client import ResourceClient

    client = ResourceClient()

    # Inspect discovered resources (populated via Python entry points).
    print(client.resources.keys())
    print(client.linked_services.keys())
    print(client.datasets.keys())
    print(client.serializers.keys())

    dataset = client.dataset(config={"type": "dataset.example", "version": "1.0.0"})
    linked_service = client.linked_service(config={"type": "linked_service.example", "version": "1.0.0"})
    serializer = client.serializer(config={"type": "serializer.example", "version": "1.0.0"})

    linked_service.connect()
    print(linked_service.connection)
    print(dataset.read())
"""

from functools import lru_cache
from importlib import import_module
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, cast

import yaml
from ds_common_logger_py_lib import Logger
from ds_common_serde_py_lib.errors import DeserializationError

from ...libs.utils import import_string, sanitize_version
from ..resource.dataset.base import Dataset, DatasetInfo
from ..resource.linked_service.base import LinkedService, LinkedServiceInfo
from ..serde.serialize import BUILTIN_SERIALIZER_INFOS
from ..serde.serialize.base import DataSerializer, SerializerInfo

logger = Logger.get_logger(__name__, package=True)


class ResourceClient:
    PROTOCOL_GROUP = "ds.protocols"
    PROVIDER_GROUP = "ds.providers"

    def __init__(self) -> None:
        super().__init__()
        self._resource_dict: dict[str, dict[str, Any]] = {}
        self._linked_services: dict[tuple[str, str], LinkedServiceInfo] = {}
        self._datasets: dict[tuple[str, str], DatasetInfo] = {}
        self._serializers: dict[tuple[str, str], SerializerInfo] = {}
        self._load_builtin_serializers()
        self._discover_resources(self.PROTOCOL_GROUP)
        self._discover_resources(self.PROVIDER_GROUP)
        logger.debug(f"Loaded {len(self._resource_dict)} resources")
        logger.debug(f"Loaded {len(self._linked_services)} linked services")
        logger.debug(f"Loaded {len(self._datasets)} datasets")
        logger.debug(f"Loaded {len(self._serializers)} serializers")

    @classmethod
    @lru_cache(maxsize=1)
    def get_instance(cls) -> "ResourceClient":
        """Get the singleton instance of ResourceClient."""
        return cls()

    @property
    def resources(self) -> dict[str, dict[str, Any]]:
        return self._resource_dict

    @property
    def linked_services(self) -> dict[tuple[str, str], LinkedServiceInfo]:
        return self._linked_services

    @property
    def datasets(self) -> dict[tuple[str, str], DatasetInfo]:
        return self._datasets

    @property
    def serializers(self) -> dict[tuple[str, str], SerializerInfo]:
        return self._serializers

    def _load_builtin_serializers(self) -> None:
        """Register built-in serializers shipped with this library."""
        for serializer_info in BUILTIN_SERIALIZER_INFOS:
            self._serializers[serializer_info.key] = serializer_info

    def _discover_resources(self, group: str) -> None:
        """
        Discover protocol/provider packages via entry points.
        Each entry point must target a Python package that contains resource.yaml in its root.
        """
        try:
            eps = entry_points(group=group)
        except Exception as exc:
            logger.warning(f"Failed to read entry points for {group}: {exc}")
            return

        for ep in eps:
            try:
                module = import_module(ep.module)
                module_path = getattr(module, "__file__", None)
                if not module_path:
                    logger.warning(f"Entry point {ep.name} has no __file__; skipping.")
                    continue

                real_path = str(Path(module_path).parent.resolve())
                self._scan_resource_directory(real_path)

            except Exception as exc:
                logger.error(f"Error when loading entry point {ep.name} ({group}): {exc}")

    def _scan_resource_directory(self, resource_dir: str) -> None:
        """
        Scan a resource directory for resource.yaml.
        Checks root first (new behavior), then subdirectories (old behavior).
        Args:
            resource_dir: Path to the resource directory.
        """
        resource_path = Path(resource_dir)
        if not resource_path.exists():
            logger.debug(f"Resource directory {resource_dir} does not exist")
            return

        self._load_resource_from_path(str(resource_path))

    def _load_resource_from_path(self, path: str) -> None:
        """
        Load resource configuration from a directory path.

        Args:
            path: Path to the resource directory.
        """
        resource_dir = Path(path)
        resource_yaml = resource_dir / "resource.yaml"
        if not resource_yaml.exists():
            logger.debug(f"No resource.yaml found in {path}")
            return

        try:
            with Path(resource_yaml).open() as f:
                resource_config = yaml.safe_load(f)
                if not resource_config:
                    logger.warning(f"Empty resource configuration in {resource_yaml}")
                    return

                resource_name = resource_config.get("name", resource_dir.name)
                self._resource_dict[resource_name] = resource_config
                self._parse_linked_services(resource_config)
                self._parse_datasets(resource_config)
                self._parse_serializers(resource_config)
        except Exception as exc:
            logger.error(f"Error loading resource configuration from {resource_yaml}: {exc}")

    def _parse_linked_services(self, config: dict[str, Any]) -> None:
        """
        Parse linked services from resource configuration.

        Args:
            config: Resource configuration dictionary.
        """
        linked_services = config.get("linked_service", [])
        for service in linked_services:
            service_name = service.get("name")
            if service_name:
                type = service.get("type")
                version = service.get("version", "1.0.0")
                service_info = LinkedServiceInfo(
                    type=type,
                    name=service_name,
                    class_name=service.get("class_name"),
                    version=version,
                    description=service.get("description"),
                )
                # Store by composite key (type, version) to support multiple versions
                self._linked_services[service_info.key] = service_info

    def _parse_datasets(self, config: dict[str, Any]) -> None:
        """
        Parse datasets from resource configuration.

        Args:
            config: Resource configuration dictionary.
        """
        datasets = config.get("dataset", [])
        for dataset in datasets:
            dataset_name = dataset.get("name")
            if dataset_name:
                type = dataset.get("type")
                version = dataset.get("version", "1.0.0")
                dataset_info = DatasetInfo(
                    type=type,
                    name=dataset_name,
                    class_name=dataset.get("class_name"),
                    version=version,
                    description=dataset.get("description"),
                )
                self._datasets[dataset_info.key] = dataset_info

    def _parse_serializers(self, config: dict[str, Any]) -> None:
        """
        Parse serializers from resource configuration.

        Args:
            config: Resource configuration dictionary.
        """
        serializers = config.get("serde", [])
        for serializer in serializers:
            serializer_name = serializer.get("name")
            if serializer_name:
                type = serializer.get("type")
                version = serializer.get("version", "1.0.0")
                serializer_info = SerializerInfo(
                    type=type,
                    name=serializer_name,
                    class_name=serializer.get("class_name"),
                    version=version,
                    description=serializer.get("description"),
                )
                self._serializers[serializer_info.key] = serializer_info

    def _get_dataset_model_cls(self, _type: str, version: str) -> type[Dataset[Any, Any, Any, Any]]:
        """
        Get a dataset model class by type and optionally version.

        Args:
            _type: str
            version: str
        Returns:
            Type[Dataset]
        """
        cls_name = self.datasets[(_type, version)].class_name
        logger.debug("Dataset Class Name: %s", cls_name)
        return cast("type[Dataset[Any, Any, Any, Any]]", import_string(cls_name))

    def _get_linked_service_model_cls(self, _type: str, version: str) -> type[LinkedService[Any]]:
        """
        Get a linked service model class by type and version.

        Args:
            _type: The type of the linked service.
            version: str version of the linked service.
        Returns:
            Type[LinkedService]
        """
        cls_name = self.linked_services[(_type, version)].class_name
        logger.debug("Linked Service Class Name: %s", cls_name)
        return cast("type[LinkedService[Any]]", import_string(cls_name))

    def _get_serializer_model_cls(self, _type: str, version: str) -> type[DataSerializer]:
        """
        Get a serializer model class by type and version.

        Args:
            _type: The type of the serializer.
            version: str version of the serializer.
        Returns:
            Type[DataSerializer]
        """
        cls_name = self.serializers[(_type, version)].class_name
        logger.debug("Serializer Class Name: %s", cls_name)
        return cast("type[DataSerializer]", import_string(cls_name))

    def linked_service(self, config: dict[str, Any]) -> LinkedService[Any]:
        """
        Get a linked service instance by configuration.

        Args:
            config: dict containing at least 'type' and 'version'
        Returns:
            LinkedService
        Raises:
            DeserializationError: If the linked service cannot be deserialized.
        """
        try:
            type = config["type"]
            version = sanitize_version(config["version"])
            model_cls = self._get_linked_service_model_cls(type, version)
            linked_service: LinkedService[Any] = model_cls.deserialize(config)
            return linked_service
        except (TypeError, KeyError) as exc:
            logger.error(f"Error deserializing linked service: {exc}")
            raise DeserializationError(
                message=f"Error deserializing linked service: {exc}",
                details={"config": config, "error": str(exc)},
            ) from exc

    def dataset(self, config: dict[str, Any]) -> Dataset[Any, Any, Any, Any]:
        """
        Get a dataset instance by configuration.

        Args:
            config: dict containing at least 'type' and 'version'
        Returns:
            Dataset
        Raises:
            DeserializationError: If the dataset cannot be deserialized.
        """
        try:
            type = config["type"]
            version = sanitize_version(config["version"])
            dataset_cls = self._get_dataset_model_cls(type, version)
            dataset: Dataset[Any, Any, Any, Any] = dataset_cls.deserialize(config)
            return dataset
        except (TypeError, KeyError) as exc:
            logger.error(f"Error deserializing dataset: {exc}")
            raise DeserializationError(
                message=f"Error deserializing dataset: {exc}",
                details={"config": config, "error": str(exc)},
            ) from exc

    def serializer(self, config: dict[str, Any]) -> DataSerializer:
        """
        Get a serializer instance by configuration.

        Args:
            config: dict containing at least 'type' and 'version'
        Returns:
            DataSerializer
        Raises:
            DeserializationError: If the serializer cannot be created.
        """
        try:
            type = config["type"]
            version = config["version"]
            serializer_cls = self._get_serializer_model_cls(type, version)
            serializer_kwargs = {key: value for key, value in config.items() if key not in {"type", "version"}}
            if "settings" in serializer_kwargs:
                serializer: DataSerializer = serializer_cls.deserialize(serializer_kwargs)
            else:
                serializer = serializer_cls(**serializer_kwargs)
            return serializer
        except (TypeError, KeyError) as exc:
            logger.error(f"Error creating serializer: {exc}")
            raise DeserializationError(
                message=f"Error creating serializer: {exc}",
                details={"config": config, "error": str(exc)},
            ) from exc
