"""
**File:** ``base.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/dataset``

Description
-----------
Base dataset models and typed properties.
"""

import io
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Generic, NamedTuple, TypeVar

import pandas as pd
from ds_common_serde_py_lib import Serializable

from ...resource.linked_service.base import LinkedService
from ...serde.deserialize.base import DataDeserializer
from ...serde.serialize.base import DataSerializer


class DatasetInfo(NamedTuple):
    """
    NamedTuple that represents the dataset information.
    """

    kind: str
    name: str
    class_name: str
    version: str
    description: str | None = None

    def __str__(self) -> str:
        """
        Return a string representation of the dataset info.

        Returns:
            A string representation of the dataset info.
        """
        return f"{self.kind}:v{self.version}"

    @property
    def key(self) -> tuple[str, str]:
        """
        Return the composite key (kind, version) for dictionary lookups.

        Returns:
            A tuple containing the kind and version.
        """
        return (self.kind, self.version)


@dataclass(kw_only=True)
class DatasetTypedProperties(Serializable):
    """
    The object containing the typed properties of the dataset.
    """

    pass


DatasetTypedPropertiesType = TypeVar("DatasetTypedPropertiesType", bound=DatasetTypedProperties)
LinkedServiceType = TypeVar("LinkedServiceType", bound=LinkedService[Any])
SerializerType = TypeVar("SerializerType", bound=DataSerializer)
DeserializerType = TypeVar("DeserializerType", bound=DataDeserializer)


@dataclass(kw_only=True)
class Dataset(
    ABC,
    Serializable,
    Generic[LinkedServiceType, DatasetTypedPropertiesType, SerializerType, DeserializerType],
):
    """
    The ds workflow nested object which identifies data within a data store,
    such as table, files, folders and documents.

    You probably want to use the subclasses and not this class directly.
    """

    typed_properties: DatasetTypedPropertiesType
    linked_service: LinkedServiceType

    serializer: SerializerType | None = None
    deserializer: DeserializerType | None = None

    post_fetch_callback: Callable[..., Any] | None = None
    prepare_write_callback: Callable[..., Any] | None = None

    content: Any | None = None
    schema: dict[str, Any] | None = None
    next: bool | None = True
    cursor: str | None = None

    @property
    @abstractmethod
    def kind(self) -> StrEnum:
        """
        Get the kind of the dataset.
        """
        raise NotImplementedError("Method (kind) not implemented")

    @abstractmethod
    def create(self, **kwargs: Any) -> Any:
        """
        Create the dataset.

        Args:
            **kwargs: The keyword arguments to pass to the create method.

        Returns:
            The result of the create method.
        """
        raise NotImplementedError("Method (create) not implemented")

    @abstractmethod
    def read(self, **kwargs: Any) -> Any:
        """
        Read the dataset.

        Args:
            **kwargs: The keyword arguments to pass to the read method.

        Returns:
            The result of the read method.
        """
        raise NotImplementedError("Method (read) not implemented")

    @abstractmethod
    def delete(self, **kwargs: Any) -> Any:
        """
        Delete the dataset.

        Args:
            **kwargs: The keyword arguments to pass to the delete method.

        Returns:
            The result of the delete method.
        """
        raise NotImplementedError("Method (delete) not implemented")

    @abstractmethod
    def update(self, **kwargs: Any) -> Any:
        """
        Update the dataset.

        Args:
            **kwargs: The keyword arguments to pass to the update method.

        Returns:
            The result of the update method.
        """
        raise NotImplementedError("Method (update) not implemented")

    @abstractmethod
    def rename(self, **kwargs: Any) -> Any:
        """
        Rename the dataset.

        Args:
            **kwargs: The keyword arguments to pass to the rename method.

        Returns:
            The result of the rename method.
        """
        raise NotImplementedError("Method (move) not implemented")


@dataclass(kw_only=True)
class BinaryDataset(
    Dataset[LinkedServiceType, DatasetTypedPropertiesType, SerializerType, DeserializerType],
    Generic[LinkedServiceType, DatasetTypedPropertiesType, SerializerType, DeserializerType],
):
    """
    Binary dataset object which identifies data within a data store,
    such as files, folders and documents.

    The content of the dataset is a binary file.
    """

    content: io.BytesIO = field(default_factory=io.BytesIO)
    next: bool | None = True
    cursor: str | None = None


@dataclass(kw_only=True)
class TabularDataset(
    Dataset[LinkedServiceType, DatasetTypedPropertiesType, SerializerType, DeserializerType],
    Generic[LinkedServiceType, DatasetTypedPropertiesType, SerializerType, DeserializerType],
):
    """
    Tabular dataset object which identifies data within a data store,
    such as table/csv/json/parquet/parquetdataset/ and other documents.

    The content of the dataset is a pandas DataFrame.
    """

    schema: dict[str, Any] | None = None
    content: pd.DataFrame = field(default_factory=pd.DataFrame)
    next: bool | None = True
    cursor: str | None = None
