import io
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Generic, NamedTuple, TypeVar

import pandas as pd

from ....libs.models.serializable import Serializable
from ...resource.linked_service.base import LinkedService
from ...serde.deserialize.base import DataDeserializer
from ...serde.serialize.base import DataSerializer


class DatasetInfo(NamedTuple):
    kind: str
    name: str
    class_name: str
    version: str
    description: str | None = None

    def __str__(self) -> str:
        """Return a string representation of the dataset info."""
        return f"{self.kind}:v{self.version}"

    @property
    def key(self) -> tuple[str, str]:
        """Return the composite key (kind, version) for dictionary lookups."""
        return (self.kind, self.version)


@dataclass(kw_only=True)
class DatasetTypedProperties(Serializable):
    """
    The object containing the typed properties of the dataset.
    """

    pass


DatasetTypedPropertiesType = TypeVar("DatasetTypedPropertiesType", bound=DatasetTypedProperties)
LinkedServiceType = TypeVar("LinkedServiceType", bound=LinkedService[Any])


@dataclass(kw_only=True)
class Dataset(
    ABC,
    Serializable,
    Generic[LinkedServiceType, DatasetTypedPropertiesType],
):
    """
    The ds workflow nested object which identifies data within a data store,
    such as table, files, folders and documents.

    You probably want to use the subclasses and not this class directly.
    """

    typed_properties: DatasetTypedPropertiesType
    linked_service: LinkedServiceType

    serializer: DataSerializer | None = None
    deserializer: DataDeserializer | None = None

    post_fetch_callback: Callable[..., Any] | None = None
    prepare_write_callback: Callable[..., Any] | None = None

    content: Any | None = None
    schema: dict[str, Any] | None = None
    next: bool | None = True
    cursor: str | None = None

    def _inject_linked_service(self, linked_service: LinkedServiceType) -> None:
        """
        Inject the linked service into the dataset.
        """
        self.linked_service = linked_service

    @property
    @abstractmethod
    def kind(self) -> str:
        """
        Get the kind of the dataset.
        """
        raise NotImplementedError("Method (kind) not implemented")

    @abstractmethod
    def create(self, **kwargs: Any) -> Any:
        """
        Create the dataset.
        :param kwargs: dict
        :return: None
        """
        raise NotImplementedError("Method (create) not implemented")

    @abstractmethod
    def read(self, **kwargs: Any) -> Any:
        """
        Read the dataset.
        :param kwargs: dict
        :return: None
        """
        raise NotImplementedError("Method (read) not implemented")

    @abstractmethod
    def delete(self, **kwargs: Any) -> Any:
        """
        Delete the dataset.
        :param kwargs: dict
        :return: None
        """
        raise NotImplementedError("Method (delete) not implemented")

    @abstractmethod
    def update(self, **kwargs: Any) -> Any:
        """
        Update the dataset.
        :param kwargs: dict
        :return: None
        """
        raise NotImplementedError("Method (update) not implemented")

    @abstractmethod
    def rename(self, **kwargs: Any) -> Any:
        """
        Move the dataset.
        :param kwargs: dict
        :return: None
        """
        raise NotImplementedError("Method (move) not implemented")


@dataclass(kw_only=True)
class BinaryDataset(
    Dataset[LinkedServiceType, DatasetTypedPropertiesType],
    Generic[LinkedServiceType, DatasetTypedPropertiesType],
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
    Dataset[LinkedServiceType, DatasetTypedPropertiesType],
    Generic[LinkedServiceType, DatasetTypedPropertiesType],
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
