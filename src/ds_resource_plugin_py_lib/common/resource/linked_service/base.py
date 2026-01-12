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
from typing import Any, Generic, NamedTuple, TypeVar

from ds_common_serde_py_lib import Serializable


class LinkedServiceInfo(NamedTuple):
    """
    NamedTuple that represents the linked service information.
    """

    kind: str
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
class LinkedServiceTypedProperties(Serializable):
    """
    Base class for linked service typed properties.
    """

    pass


LinkedServiceTypedPropertiesType = TypeVar("LinkedServiceTypedPropertiesType", bound=LinkedServiceTypedProperties)


@dataclass(kw_only=True)
class LinkedService(
    ABC,
    Serializable,
    Generic[LinkedServiceTypedPropertiesType],
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

    typed_properties: LinkedServiceTypedPropertiesType

    @property
    @abstractmethod
    def kind(self) -> StrEnum:
        """
        Get the kind of the linked service.

        Returns:
            The kind of the linked service.
        """
        raise NotImplementedError("kind property is not implemented")

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
