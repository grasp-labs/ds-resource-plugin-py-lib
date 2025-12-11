import logging
from typing import Any

from ds_common_logger_py_lib import LoggingMixin


class DataSerializer(LoggingMixin):
    """
    Extensible class to serialize dataset content.

    Convert obj to bytes.

    Not supposed to be used directly, but to be subclassed.
    """

    log_level = logging.DEBUG

    def __call__(self, obj: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
