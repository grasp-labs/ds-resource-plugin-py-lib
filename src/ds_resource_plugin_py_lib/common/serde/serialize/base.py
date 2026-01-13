"""
**File:** ``base.py``
**Region:** ``ds_resource_plugin_py_lib/common/serde/serialize``

Description
-----------
Base classes for serializers.
"""

import logging
from dataclasses import dataclass
from typing import Any

from ds_common_logger_py_lib import LoggingMixin
from ds_common_serde_py_lib import Serializable


@dataclass(kw_only=True)
class DataSerializer(Serializable, LoggingMixin):
    """
    Extensible class to serialize dataset content.

    Convert obj to bytes.

    Not supposed to be used directly, but to be subclassed.
    """

    log_level = logging.DEBUG

    def __call__(self, obj: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
