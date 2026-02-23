"""
**File:** ``base.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/linked_service``

Description
-----------
Base models for linked services.
"""

import uuid
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

    id: uuid.UUID
    name: str
    description: str | None = None
    version: str

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
        ...

    @property
    @abstractmethod
    def connection(self) -> Any:
        """
        Return the backend client or connection object. Must raise
        ``ConnectionError`` if ``connect()`` has not been called.

        Returns:
            The backend client, session, or connection object.

        Raises:
            ConnectionError: If the connection has not been established.

        See Also:
            Full contract: ``docs/LINKED_SERVICE_CONTRACT.md`` -- ``connection``
        """
        ...

    @abstractmethod
    def connect(self) -> None:
        """
        Establish a connection to the backend data store. The result is
        stored internally and accessible via the ``connection`` property.

        Raises:
            ConnectionError: If the connection cannot be established.
            AuthenticationError: If credentials are invalid.
            NotSupportedError: If the provider does not support connect.

        See Also:
            Full contract: ``docs/LINKED_SERVICE_CONTRACT.md`` -- ``connect()``
        """
        ...

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """
        Verify that the connection to the backend is healthy. Does not
        raise on connection failure -- returns ``(False, "reason")``
        instead.

        Returns:
            A tuple ``(success, message)``. On success: ``(True, "")``.
            On failure: ``(False, "error description")``.

        Raises:
            NotSupportedError: If the provider does not support test_connection.

        See Also:
            Full contract: ``docs/LINKED_SERVICE_CONTRACT.md`` -- ``test_connection()``
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """
        Release connections, sessions, or handles. Must not raise if
        already closed. Idempotent.

        See Also:
            Full contract: ``docs/LINKED_SERVICE_CONTRACT.md`` -- ``close()``
        """
        ...
