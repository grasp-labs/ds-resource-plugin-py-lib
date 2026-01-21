"""
**File:** ``base.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/linked_service``

Description
-----------
Base models for linked services.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from types import TracebackType
from typing import Any, Generic, NamedTuple, Self, TypeVar

from ds_common_serde_py_lib import Serializable


class LinkedServiceInfo(NamedTuple):
    """
    NamedTuple that represents the linked service information.
    """

    type: str
    name: str
    class_name: str
    version: str
    description: str | None = None

    def __str__(self) -> str:
        """
        Return a string representation of the linked service info.

        Returns:
            A string representation of the linked service info.
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
class LinkedServiceSettings(Serializable):
    """
    The object containing the settings of the linked service.
    """

    pass


LinkedServiceSettingsType = TypeVar("LinkedServiceSettingsType", bound=LinkedServiceSettings)


@dataclass(kw_only=True)
class LinkedService(
    ABC,
    Serializable,
    Generic[LinkedServiceSettingsType],
):
    """
    The object containing the connection information to connect with related data store.

    You probably want to use the subclasses and not this class directly.
    Known subclasses are:
    - SftpLinkedService
    - S3LinkedService
    - GraphQlLinkedService

    All required parameters must be populated in the constructor in order to send to ds-workflow-service.
    """

    settings: LinkedServiceSettingsType

    def __enter__(self) -> Self:
        """
        Context manager enter.

        Returns:
            The linked service.
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
    def type(self) -> StrEnum:
        """
        Get the type of the linked service.

        Returns:
            The type of the linked service.
        """
        raise NotImplementedError("type property is not implemented")

    @abstractmethod
    def connect(self) -> Any:
        """
        Connect to the data store.

        Returns:
            The result of the connect method.
        """
        raise NotImplementedError("connect method is not implemented")

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """
        Test the connection to the data store.

        Returns:
            A tuple containing a boolean indicating if the
            connection is successful and a string containing the error message.
        """
        raise NotImplementedError("test_connection method is not implemented")

    @abstractmethod
    def close(self) -> None:
        """
        Close the linked service.

        Returns:
            None.
        """
        raise NotImplementedError("close method is not implemented")
