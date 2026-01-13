"""
**File:** ``import_string.py``
**Region:** ``ds_resource_plugin_py_lib/libs/utils``

Description
-----------
Utility function to import a dotted module path and return the attribute/class designated by the last name in the path.

Example
-------
.. code-block:: python

    from ds_resource_plugin_py_lib.libs.utils.import_string import import_string

    # Import a symbol by dotted path.
    json_loads = import_string("json.loads")
    result = json_loads('{"a": 1}')
"""

from importlib import import_module
from typing import Any

from ds_common_logger_py_lib import Logger

logger = Logger.get_logger(__name__)


def import_string(dotted_path: str) -> Any:
    """
    Import a dotted module path and return the attribute/class designated by the last name in the path.
    Args:
        dotted_path: The dotted module path to import.

    Returns:
        The attribute/class designated by the last name in the path.

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
