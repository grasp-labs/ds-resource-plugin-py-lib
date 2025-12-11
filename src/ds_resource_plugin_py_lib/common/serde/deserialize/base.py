import logging
from typing import Any

from ds_common_logger_py_lib import LoggingMixin


class DataDeserializer(LoggingMixin):
    """
    Extensible class to deserialize dataset content.

    Not supposed to be used directly, but to be subclassed.
    """

    log_level = logging.DEBUG

    def __call__(self, value: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def get_next(self, _value: Any, **_kwargs: Any) -> bool:
        return False

    def get_end_cursor(self, _value: Any, **_kwargs: Any) -> str | None:
        return None
