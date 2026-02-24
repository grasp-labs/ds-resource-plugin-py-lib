"""
**File:** ``base.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/dataset``

Description
-----------
Base dataset models and typed properties.
"""

import io
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from types import TracebackType
from typing import Any, Generic, NamedTuple, Self, TypeVar

import pandas as pd
from ds_common_serde_py_lib import Serializable

from ...resource.linked_service.base import LinkedService
from ...serde.deserialize.base import DataDeserializer
from ...serde.serialize.base import DataSerializer
from .decorators import track_result
from .enums import DatasetMethod
from .result import OperationInfo


class DatasetInfo(NamedTuple):
    """
    NamedTuple that represents the dataset information.
    """

    type: str
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
        return f"{self.type}:v{self.version}"

    @property
    def key(self) -> tuple[str, str]:
        """
        Return the composite key (type, version) for dictionary lookups.

        Returns:
            A tuple containing the type and version.
        """
        return (self.type, self.version)


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

    id: uuid.UUID
    name: str
    description: str | None = None
    version: str

    settings: DatasetSettingsType
    linked_service: LinkedServiceType

    serializer: SerializerType | None = None
    deserializer: DeserializerType | None = None

    input: Any | None = field(default=None, metadata={"serialize": False})
    output: Any | None = field(default=None, metadata={"serialize": False})

    checkpoint: dict[str, Any] = field(default_factory=dict)
    operation: OperationInfo = field(default_factory=OperationInfo)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Initialize the subclass.

        Args:
            kwargs: The keyword arguments.

        Returns:
            The subclass.
        """
        super().__init_subclass__(**kwargs)
        for name in DatasetMethod.all_values():
            method = cls.__dict__.get(name)
            if method is not None and not getattr(method, "_tracked", False):
                setattr(cls, name, track_result(method))

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
    def supports_checkpoint(self) -> bool:
        """Whether this provider supports incremental loads via ``self.checkpoint``."""
        return False

    @property
    @abstractmethod
    def type(self) -> StrEnum:
        """
        Get the type of the dataset.
        """
        ...

    @abstractmethod
    def create(self) -> None:
        """
        Insert all rows in ``self.input`` into the target as a single atomic
        transaction. Must not delete, update, or overwrite existing data.

        Raises:
            CreateError: If the operation fails.
            NotSupportedError: If the provider does not support create.

        See Also:
            Full contract: ``docs/DATASET_CONTRACT.md`` -- ``create()``
        """
        ...

    @abstractmethod
    def read(self) -> None:
        """
        Read data from the source and assign it to ``self.output``.
        Pagination within a single call is handled internally.
        Supports incremental loads via ``self.checkpoint``.

        Raises:
            ReadError: If the operation fails.
            NotSupportedError: If the provider does not support read.

        See Also:
            Full contract: ``docs/DATASET_CONTRACT.md`` -- ``read()``
        """
        ...

    @abstractmethod
    def update(self) -> None:
        """
        Update existing rows in the target matched by identity columns
        defined in ``self.settings``. Atomic. Must not insert new rows.

        Raises:
            UpdateError: If the operation fails.
            NotSupportedError: If the provider does not support update.

        See Also:
            Full contract: ``docs/DATASET_CONTRACT.md`` -- ``update()``
        """
        ...

    @abstractmethod
    def upsert(self) -> None:
        """
        Insert rows that do not exist, update rows that do, matched by
        identity columns defined in ``self.settings``. Atomic.

        Raises:
            UpsertError: If the operation fails.
            NotSupportedError: If the provider does not support upsert.

        See Also:
            Full contract: ``docs/DATASET_CONTRACT.md`` -- ``upsert()``
        """
        ...

    @abstractmethod
    def delete(self) -> None:
        """
        Remove specific rows from the target matched by identity columns
        defined in ``self.settings``. Atomic. Idempotent.

        Raises:
            DeleteError: If the operation fails.
            NotSupportedError: If the provider does not support delete.

        See Also:
            Full contract: ``docs/DATASET_CONTRACT.md`` -- ``delete()``
        """
        ...

    @abstractmethod
    def purge(self) -> None:
        """
        Remove all content from the target. ``self.input`` is not used.
        Atomic. Idempotent.

        Raises:
            PurgeError: If the operation fails.
            NotSupportedError: If the provider does not support purge.

        See Also:
            Full contract: ``docs/DATASET_CONTRACT.md`` -- ``purge()``
        """
        ...

    @abstractmethod
    def list(self) -> None:
        """
        Discover available resources and populate ``self.output`` with a
        DataFrame of resources and their metadata. Idempotent.

        Raises:
            ListError: If the operation fails.
            NotSupportedError: If the provider does not support listing.

        See Also:
            Full contract: ``docs/DATASET_CONTRACT.md`` -- ``list()``
        """
        ...

    @abstractmethod
    def rename(self) -> None:
        """
        Rename the resource in the backend. Atomic. Not idempotent.

        Raises:
            RenameError: If the operation fails.
            NotSupportedError: If the provider does not support renaming.

        See Also:
            Full contract: ``docs/DATASET_CONTRACT.md`` -- ``rename()``
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """
        Release any connections, sessions, or handles held by the linked
        service. Must not raise if already closed. Idempotent.

        See Also:
            Full contract: ``docs/DATASET_CONTRACT.md`` -- ``close()``
        """
        ...


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

    input: io.BytesIO = field(default_factory=io.BytesIO, metadata={"serialize": False})
    output: io.BytesIO = field(default_factory=io.BytesIO, metadata={"serialize": False})


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

    input: pd.DataFrame = field(default_factory=pd.DataFrame, metadata={"serialize": False})
    output: pd.DataFrame = field(default_factory=pd.DataFrame, metadata={"serialize": False})
