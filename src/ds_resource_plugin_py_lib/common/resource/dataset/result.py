"""
**File:** ``result.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/dataset``

Description
-----------
Dataclass capturing operation details for every dataset method call.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ds_common_serde_py_lib import Serializable

from .enums import DatasetMethod


@dataclass(kw_only=True)
class OperationError(Serializable):
    """Structured error captured from a ``ResourceException``."""

    message: str
    """The error message."""
    code: str
    """The error code."""
    status_code: int
    """The HTTP status code."""
    details: dict[str, Any] = field(default_factory=dict)
    """The error details."""


@dataclass(kw_only=True)
class OperationInfo(Serializable):
    """
    Report produced by every dataset operation.

    Timing fields (``started_at``, ``ended_at``, ``duration_ms``) are
    populated automatically by the ``track_result`` decorator.  Providers
    may set ``row_count``, ``schema``, or ``metadata`` inside their
    method; any value left at its default will be auto-derived from
    ``self.output`` after the method returns.

    Accessible on the dataset instance as ``self.operation``.
    """

    method: DatasetMethod | None = None
    """The method that was called."""
    success: bool = False
    """Whether the method call was successful."""
    error: OperationError | None = None
    """The error captured from a ``ResourceException``."""
    row_count: int = 0
    """The number of rows read, written, or discovered."""
    started_at: datetime | None = None
    """The timestamp when the method started."""
    ended_at: datetime | None = None
    """The timestamp when the method ended."""
    duration_ms: float = 0.0
    """The duration of the method in milliseconds."""
    schema: dict[str, Any] | None = None
    """The schema of the data."""
    metadata: dict[str, Any] = field(default_factory=dict)
    """The metadata of the data."""
