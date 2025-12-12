"""
A Python package from the ds-resource-plugin library.

**File:** ``__init__.py``
**Region:** ``ds-resource-plugin-py-lib``

Example:

.. code-block:: python

    from ds_resource_plugin_py_lib import __version__

    print(f"Package version: {__version__}")
"""

from pathlib import Path

from . import common, libs

_VERSION_FILE = Path(__file__).parent.parent.parent / "VERSION.txt"
__version__ = _VERSION_FILE.read_text().strip() if _VERSION_FILE.exists() else "0.0.0"

__all__ = [
    "__version__",
    "common",
    "libs",
]
