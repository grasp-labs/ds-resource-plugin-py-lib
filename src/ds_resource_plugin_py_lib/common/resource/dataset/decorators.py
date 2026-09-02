"""
**File:** ``decorators.py``
**Region:** ``ds_resource_plugin_py_lib/common/resource/dataset``

Description
-----------
Decorators applied automatically to dataset method overrides via
``Dataset.__init_subclass__``.
"""

import functools
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .enums import DatasetMethod
from .result import OperationError, OperationInfo


def track_result(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Wrap a dataset method so that ``self.operation`` is initialised before the
    call and enriched afterwards.

    **Auto-populated fields:**

    - ``method`` -- set to the function name.
    - ``success`` -- ``True`` when the method returns without raising.
    - ``error`` -- structured ``OperationError`` captured from
      ``ResourceException`` on failure.
    - ``started_at`` / ``ended_at`` / ``duration_ms`` -- wall-clock timing.
    - ``row_count`` -- derived from ``len(self.output)`` when the
      provider leaves the default (``0``).
    - ``schema`` -- derived via PyArrow dtype inference on ``self.output``
      (``self.output.convert_dtypes(dtype_backend="pyarrow")``), unless the
      provider already set ``self.operation.schema`` explicitly.

    On data-producing methods (see ``DatasetMethod.row_schema_validated_values``),
    if the dataset declares ``self.row_schema`` (portable, engine-agnostic
    ``dict[str, str]`` table/row contract -- see ``TabularDataset.row_schema``;
    distinct from any JSON Schema), ``self.output`` is validated against it
    via ``self._validate_output_row_schema()``. That check runs *after* the
    ``schema`` auto-derivation above and reuses ``self.operation.schema``
    rather than re-running the PyArrow conversion -- do not reorder these
    two blocks. Both sides are normalized via
    ``dataset.dtype.normalize_row_schema`` before comparison, so a declared
    ``"int64"`` matches pandas' raw ``"int64[pyarrow]"``. If a provider
    explicitly overrides ``self.operation.schema`` with a custom value,
    row schema validation compares against that overridden value rather
    than the true output dtypes. Mismatches raise
    ``RowSchemaValidationError``, which is captured the same way as any
    other exception below.

    Providers may override any of these by assigning to ``self.operation``
    inside their method body.

    """

    @functools.wraps(fn)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        self.operation = OperationInfo(method=DatasetMethod(fn.__name__))
        self.operation.started_at = datetime.now(tz=UTC)
        try:
            fn(self, *args, **kwargs)

            self.operation.success = True

            if self.operation.row_count == 0 and hasattr(self.output, "__len__"):
                self.operation.row_count = len(self.output)

            if self.operation.schema is None and hasattr(self.output, "convert_dtypes"):
                converted = self.output.convert_dtypes(dtype_backend="pyarrow")
                self.operation.schema = {str(col): str(dtype) for col, dtype in converted.dtypes.to_dict().items()}

            if (
                getattr(self, "row_schema", None) is not None
                and hasattr(self, "_validate_output_row_schema")
                and fn.__name__ in DatasetMethod.row_schema_validated_values()
            ):
                self._validate_output_row_schema()

        except Exception as exc:
            self.operation.success = False
            self.operation.error = OperationError(
                message=getattr(exc, "message", str(exc)),
                code=getattr(exc, "code", type(exc).__name__),
                status_code=getattr(exc, "status_code", 500),
                details=getattr(exc, "details", {}),
            )
            raise

        finally:
            self.operation.ended_at = datetime.now(tz=UTC)
            delta = self.operation.ended_at - self.operation.started_at
            self.operation.duration_ms = round(delta.total_seconds() * 1000, 3)

    wrapper._tracked = True  # type: ignore[attr-defined]
    return wrapper
