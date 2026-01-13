"""
**File:** ``__init__.py``
**Region:** ``ds_resource_plugin_py_lib``

Description
-----------
A Python package from the ds-resource-plugin library.

Example
-------
.. code-block:: python

    from ds_resource_plugin_py_lib import __version__

    print(f"Package version: {__version__}")
"""

from importlib.metadata import version

from . import common, libs

__version__ = version("ds-resource-plugin-py-lib")

__all__ = [
    "__version__",
    "common",
    "libs",
]
