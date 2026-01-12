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

    dataset = client.dataset(config={"kind": "dataset.example", "version": "1.0.0"})
    linked_service = client.linked_service(config={"kind": "linked_service.example", "version": "1.0.0"})

    print(linked_service.connect())
    print(dataset.read())
"""

import logging
from functools import lru_cache
from importlib import import_module
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, cast

import yaml
from ds_common_logger_py_lib.mixin import LoggingMixin
from ds_common_serde_py_lib.errors import DeserializationError

from ...libs.utils.import_string import import_string
from ..resource.dataset.base import Dataset, DatasetInfo
from ..resource.linked_service.base import LinkedService, LinkedServiceInfo


class ResourceClient(LoggingMixin):
    log_level = logging.DEBUG

    PROTOCOL_GROUP = "ds.protocols"
    PROVIDER_GROUP = "ds.providers"

    def __init__(self) -> None:
        super().__init__()
        self._resource_dict: dict[str, dict[str, Any]] = {}
        self._linked_services: dict[tuple[str, str], LinkedServiceInfo] = {}
        self._datasets: dict[tuple[str, str], DatasetInfo] = {}
        self._discover_resources(self.PROTOCOL_GROUP)
        self._discover_resources(self.PROVIDER_GROUP)
        self.log.debug(f"Loaded {len(self._resource_dict)} resources")
        self.log.debug(f"Loaded {len(self._linked_services)} linked services")
        self.log.debug(f"Loaded {len(self._datasets)} datasets")

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

    def _discover_resources(self, group: str) -> None:
        """
        Discover protocol/provider packages via entry points.
        Each entry point must target a Python package that contains resource.yaml in its root.
        """
        try:
            eps = entry_points(group=group)
        except Exception as exc:
            self.log.warning(f"Failed to read entry points for {group}: {exc}")
            return

        for ep in eps:
            try:
                module = import_module(ep.module)
                module_path = getattr(module, "__file__", None)
                if not module_path:
                    self.log.warning(f"Entry point {ep.name} has no __file__; skipping.")
                    continue

                real_path = str(Path(module_path).parent.resolve())
                self._scan_resource_directory(real_path)

            except Exception as exc:
                self.log.error(f"Error when loading entry point {ep.name} ({group}): {exc}")

    def _scan_resource_directory(self, resource_dir: str) -> None:
        """
        Scan a resource directory for resource.yaml.
        Checks root first (new behavior), then subdirectories (old behavior).
        Args:
            resource_dir: Path to the resource directory.
        """
        resource_path = Path(resource_dir)
        if not resource_path.exists():
            self.log.debug(f"Resource directory {resource_dir} does not exist")
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
            self.log.debug(f"No resource.yaml found in {path}")
            return

        try:
            with Path(resource_yaml).open() as f:
                resource_config = yaml.safe_load(f)
                if not resource_config:
                    self.log.warning(f"Empty resource configuration in {resource_yaml}")
                    return

                resource_name = resource_config.get("name", resource_dir.name)
                self._resource_dict[resource_name] = resource_config
                self._parse_linked_services(resource_config)
                self._parse_datasets(resource_config)
        except Exception as exc:
            self.log.error(f"Error loading resource configuration from {resource_yaml}: {exc}")

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
                kind = service.get("kind")
                version = service.get("version", "1.0.0")
                service_info = LinkedServiceInfo(
                    kind=kind,
                    name=service_name,
                    class_name=service.get("class_name"),
                    version=version,
                    description=service.get("description"),
                )
                # Store by composite key (kind, version) to support multiple versions
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
                kind = dataset.get("kind")
                version = dataset.get("version", "1.0.0")
                dataset_info = DatasetInfo(
                    kind=kind,
                    name=dataset_name,
                    class_name=dataset.get("class_name"),
                    version=version,
                    description=dataset.get("description"),
                )
                self._datasets[dataset_info.key] = dataset_info

    def _get_dataset_model_cls(self, kind: str, version: str) -> type[Dataset[Any, Any, Any, Any]]:
        """
        Get a dataset model class by kind and optionally version.

        Args:
            kind: str
            version: str
        Returns:
            Type[Dataset]
        """
        cls_name = self.datasets[(kind, version)].class_name
        self.log.debug("Dataset Class Name: %s", cls_name)
        return cast("type[Dataset[Any, Any, Any, Any]]", import_string(cls_name))

    def _get_linked_service_model_cls(self, kind: str, version: str) -> type[LinkedService[Any]]:
        """
        Get a linked service model class by kind and version.

        Args:
            kind: The kind of the linked service.
            version: str version of the linked service.
        Returns:
            Type[LinkedService]
        """
        cls_name = self.linked_services[(kind, version)].class_name
        self.log.debug("Linked Service Class Name: %s", cls_name)
        return cast("type[LinkedService[Any]]", import_string(cls_name))

    def linked_service(self, config: dict[str, Any]) -> LinkedService[Any]:
        """
        Get a linked service instance by configuration.

        Args:
            config: dict containing at least 'kind' and 'version'
        Returns:
            LinkedService
        Raises:
            DeserializationError: If the linked service cannot be deserialized.
        """
        try:
            kind = config["kind"]
            version = config["version"]
            model_cls = self._get_linked_service_model_cls(kind, version)
            linked_service: LinkedService[Any] = model_cls.deserialize(config)
            return linked_service
        except (TypeError, KeyError) as exc:
            self.log.exception(f"Error deserializing linked service: {exc}")
            raise DeserializationError(
                message=f"Error deserializing linked service: {exc}",
                details={"config": config, "error": str(exc)},
            ) from exc

    def dataset(self, config: dict[str, Any]) -> Dataset[Any, Any, Any, Any]:
        """
        Get a dataset instance by configuration.

        Args:
            config: dict containing at least 'kind' and 'version'
        Returns:
            Dataset
        Raises:
            DeserializationError: If the dataset cannot be deserialized.
        """
        try:
            kind = config["kind"]
            version = config["version"]
            dataset_cls = self._get_dataset_model_cls(kind, version)
            dataset: Dataset[Any, Any, Any, Any] = dataset_cls.deserialize(config)
            return dataset
        except (TypeError, KeyError) as exc:
            self.log.exception(f"Error deserializing dataset: {exc}")
            raise DeserializationError(
                message=f"Error deserializing dataset: {exc}",
                details={"config": config, "error": str(exc)},
            ) from exc
