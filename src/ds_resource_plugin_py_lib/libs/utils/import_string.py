from importlib import import_module
from typing import Any

from ds_common_logger_py_lib import Logger

logger = Logger.get_logger(__name__)


def import_string(dotted_path: str) -> Any:
    """
    Import a dotted module path and return the attribute/class designated by the last name in the path.

    Raise ImportError if the import failed.
    """
    logger.info("Importing string: %s", dotted_path)
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as exc:
        raise ImportError(f"{dotted_path} doesn't look like a module path") from exc

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as exc:
        raise ImportError(f'Module "{module_path}" does not define a "{class_name}" attribute/class') from exc
