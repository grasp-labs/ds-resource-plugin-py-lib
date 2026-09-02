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
from .dtype import normalize_row_schema
from .enums import DatasetMethod
from .errors import RowSchemaValidationError
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

    row_schema: dict[str, str] | None = None
    """
    Declared column name -> portable, engine-agnostic logical type name
    (e.g. ``{"id": "int64", "name": "string", "created_at": "timestamp"}``).

    This is a table/row data contract -- **not** a JSON Schema, and not a
    place to write pandas/PyArrow implementation details. Do not confuse
    this with the provider-facing JSON Schema used to validate a dataset's
    *construction payload* before ``deserialize()`` (see
    ``DATASET_CONTRACT.md`` -- "Schema and Dataclass Alignment"); that
    schema describes the shape of this ``Dataset`` object itself
    (``id``/``name``/``version``/``settings``/...), while ``row_schema``
    describes the shape of the *data* flowing through ``self.output``.

    Write plain logical type names, not
    ``convert_dtypes(dtype_backend="pyarrow")`` output like
    ``"int64[pyarrow]"``. Common names: ``int8``/``int16``/``int32``/
    ``int64``, ``uint8``/``uint16``/``uint32``/``uint64``,
    ``float32``/``float64``, ``bool``, ``string``, ``binary``, ``date``,
    ``time``, ``timestamp``, ``decimal``. This is a normalization, not an
    enforced enum -- other names are accepted as-is (lowercased); see
    ``dataset.dtype.normalize_dtype`` for the exact rules.

    Optional. When set, ``self.output`` is validated against it after
    ``read``/``create``/``update``/``upsert``/``delete`` (see
    ``DatasetMethod.row_schema_validated_values``) -- exactly for
    ``read()``, as a subset for ``create()``/``update()``/``upsert()``/
    ``delete()`` (see ``_validate_output_row_schema`` for the full rules),
    and skipped entirely on a contract-guaranteed no-op (empty
    ``self.input`` on a write method).

    Internally, both this declared row schema and the PyArrow-backend
    dtypes pandas actually produces (``self.operation.schema``, via
    ``convert_dtypes(dtype_backend="pyarrow")``) are normalized to the same
    portable vocabulary via ``dataset.dtype.normalize_row_schema`` before
    being compared -- callers never need to know which DataFrame backend
    produced the data. ``self.operation.schema`` itself is left untouched
    (still the raw PyArrow-backend string) since it is a separate,
    general-purpose diagnostic field, not specific to row schema
    validation.
    """

    def _has_empty_input(self) -> bool:
        """True when ``self.input`` is ``None`` or empty, per the
        ``DATASET_CONTRACT.md`` "Empty input" no-op rule."""
        return self.input is None or (hasattr(self.input, "__len__") and len(self.input) == 0)

    def _validate_output_row_schema(self) -> None:
        """
        Validate ``self.output`` against the declared ``self.row_schema``.

        Reuses ``self.operation.schema`` -- already computed by
        ``track_result`` via the same ``convert_dtypes(dtype_backend="pyarrow")``
        call -- instead of re-running that (non-trivial, data-copying)
        conversion a second time. This relies on ``track_result`` populating
        ``self.operation.schema`` before invoking this method. Both
        ``self.row_schema`` and ``self.operation.schema`` are normalized via
        ``dataset.dtype.normalize_row_schema`` before comparison, so declared
        logical type names (``"int64"``) and pandas' raw PyArrow-backend
        strings (``"int64[pyarrow]"``) compare equal.

        **Skipped entirely** when:

        - ``self.row_schema`` is not declared.
        - The current method is input-dependent (``create``/``update``/
          ``upsert``/``delete``, see ``DatasetMethod.input_dependent_values``)
          and ``self.input`` is empty. This is a contract-guaranteed no-op
          (``DATASET_CONTRACT.md`` -- "Empty input"); the provider is not
          required to reset ``self.output`` on a no-op, so it may still hold
          a previous call's data (e.g. a prior ``list()``/``read()``).
          Validating stale output here would reject a call the contract
          guarantees can never fail.
        - ``self.output`` has no rows -- an empty result carries no reliable
          column/dtype information to compare (a default, uninitialised
          DataFrame has no columns at all).
        - ``self.operation.schema`` is unavailable (``self.output`` does not
          expose ``convert_dtypes``, e.g. not a DataFrame).

        **Match mode** depends on the method (see
        ``DatasetMethod.full_row_schema_match_values`` /
        ``DatasetMethod.partial_row_schema_match_values``):

        - ``read()`` -- exact match. ``self.output`` must contain every
          declared column with the declared type, and no undeclared
          columns. ``read()`` is the only row-schema-validated method with
          no ``self.output = self.input.copy()`` fallback, so its output is
          always the real backend result set.
        - ``create()`` / ``update()`` / ``upsert()`` / ``delete()`` --
          partial match. ``self.output`` may legitimately carry only a
          subset of ``self.row_schema`` (e.g. a server-assigned
          autoincrement ``id`` the caller never supplied to ``create()``,
          or identity/changed columns for ``update()``/``upsert()``/
          ``delete()``), per the ``self.output = self.input.copy()``
          fallback in ``DATASET_CONTRACT.md`` for backends with no
          ``RETURNING``-style response. Columns that *are* present are
          still checked against ``self.row_schema``; declared columns that
          are absent are not an error. Columns present but not declared in
          ``self.row_schema`` are still flagged.

        Raises:
            RowSchemaValidationError: If ``self.output`` does not match
                ``self.row_schema`` under the applicable match mode.
                ``details`` report normalized (portable) type names on both
                sides.
        """
        if self.row_schema is None:
            return

        method = self.operation.method
        if method in DatasetMethod.input_dependent_values() and self._has_empty_input():
            return

        if not hasattr(self.output, "__len__") or len(self.output) == 0:
            return

        raw_actual = self.operation.schema
        if raw_actual is None:
            return

        expected = normalize_row_schema(self.row_schema)
        actual = normalize_row_schema(raw_actual)

        if method in DatasetMethod.partial_row_schema_match_values():
            mismatched = {col: dtype for col, dtype in actual.items() if col in expected and expected[col] != dtype}
            unknown = {col: dtype for col, dtype in actual.items() if col not in expected}
            if mismatched or unknown:
                raise RowSchemaValidationError(
                    details={
                        "expected": expected,
                        "actual": actual,
                        "mismatched": mismatched,
                        "unknown": unknown,
                    },
                )
            return

        if actual != expected:
            raise RowSchemaValidationError(
                details={"expected": expected, "actual": actual},
            )
