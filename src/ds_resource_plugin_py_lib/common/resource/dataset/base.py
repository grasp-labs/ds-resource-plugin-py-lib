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
from types import TracebackType
from typing import Any, Generic, NamedTuple, Self, TypeVar

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
class DatasetSettings(Serializable):
    """
    The object containing the settings of the dataset.
    """

    pass


DatasetSettingsType = TypeVar("DatasetSettingsType", bound=DatasetSettings)
LinkedServiceType = TypeVar("LinkedServiceType", bound=LinkedService[Any])
SerializerType = TypeVar("SerializerType", bound=DataSerializer)
DeserializerType = TypeVar("DeserializerType", bound=DataDeserializer)


@dataclass(kw_only=True)
class Dataset(
    ABC,
    Serializable,
    Generic[LinkedServiceType, DatasetSettingsType, SerializerType, DeserializerType],
):
    """
    The ds workflow nested object which identifies data within a data store,
    such as table, files, folders and documents.

    You probably want to use the subclasses and not this class directly.
    """

    settings: DatasetSettingsType
    linked_service: LinkedServiceType

    serializer: SerializerType | None = None
    deserializer: DeserializerType | None = None

    post_fetch_callback: Callable[..., Any] | None = None
    prepare_write_callback: Callable[..., Any] | None = None

    input: Any | None = None
    output: Any | None = None

    schema: dict[str, Any] | None = None
    next: bool | None = True
    cursor: str | None = None

    def __enter__(self) -> Self:
        """
        Context manager enter.

        Returns:
            The dataset.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        Context manager exit.

        Args:
            exc_type: The type of the exception.
            exc_value: The value of the exception.
            traceback: The traceback of the exception.
        """
        self.close()

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

    @abstractmethod
    def close(self) -> None:
        """
        Close the dataset.

        This method is called when the dataset is closed.
        It is used to clean up the dataset and close the connection.

        Returns:
            None.
        """
        raise NotImplementedError("Method (close) not implemented")


@dataclass(kw_only=True)
class BinaryDataset(
    Dataset[LinkedServiceType, DatasetSettingsType, SerializerType, DeserializerType],
    Generic[LinkedServiceType, DatasetSettingsType, SerializerType, DeserializerType],
):
    """
    Binary dataset object which identifies data within a data store,
    such as files, folders and documents.

    The input of the dataset is a binary file.
    The output of the dataset is a binary file.
    """

    input: io.BytesIO = field(default_factory=io.BytesIO)
    output: io.BytesIO = field(default_factory=io.BytesIO)

    next: bool | None = True
    cursor: str | None = None


@dataclass(kw_only=True)
class TabularDataset(
    Dataset[LinkedServiceType, DatasetSettingsType, SerializerType, DeserializerType],
    Generic[LinkedServiceType, DatasetSettingsType, SerializerType, DeserializerType],
):
    """
    Tabular dataset object which identifies data within a data store,
    such as table/csv/json/parquet/parquetdataset/ and other documents.

    The input of the dataset is a pandas DataFrame.
    The output of the dataset is a pandas DataFrame.
    """

    input: pd.DataFrame = field(default_factory=pd.DataFrame)
    output: pd.DataFrame = field(default_factory=pd.DataFrame)

    schema: dict[str, Any] | None = None
    next: bool | None = True
    cursor: str | None = None
