"""
**File:** ``json_default.py``
**Region:** ``ds_resource_plugin_py_lib/libs/utils``

Description
-----------
JSON serialization helpers for values that are not natively JSON-encodable.

Example
-------
.. code-block:: python

    from datetime import datetime

    import json

    from ds_resource_plugin_py_lib.libs.utils.json_default import json_default

    payload = json.dumps({"created_at": datetime(2024, 3, 15, 10, 30)}, default=json_default)
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


def json_default(value: Any) -> Any:
    """
    ``default`` callback for :func:`json.dumps`.

    Maps common Python types (for example ``datetime``) to JSON-serializable
    values. Scalar-like objects with a callable ``.item()`` (for example numpy
    scalars) are unwrapped before encoding. Unknown types raise
    :class:`TypeError`, matching stdlib behavior.

    ``bytes`` and ``bytearray`` are intentionally not converted: JSON has no binary
    type, and decoding bytes as text would silently change the data.
    """
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, (set, frozenset)):
        return list(value)

    item = getattr(value, "item", None)
    if callable(item):
        native = item()
        try:
            return json_default(native)
        except TypeError:
            return native

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
