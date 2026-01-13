"""
**File:** ``test_import_string.py``
**Region:** ``tests/libs/utils``

Description
-----------
Tests for the `import_string` utility ensuring correct imports and errors.
"""

import sys
import types

import pytest

from ds_resource_plugin_py_lib.libs.utils.import_string import import_string


def test_import_string_success():
    """Import attribute from dynamically created module."""
    module = types.ModuleType("dummy.module")
    module.Sample = object
    sys.modules["dummy.module"] = module

    result = import_string("dummy.module.Sample")

    assert result is module.Sample


def test_import_string_invalid_path():
    """Raise ImportError for invalid dotted path."""
    with pytest.raises(ImportError):
        import_string("not-a-path")


def test_import_string_missing_attribute():
    """Raise ImportError when attribute is missing."""
    module = types.ModuleType("dummy.missing")
    sys.modules["dummy.missing"] = module

    with pytest.raises(ImportError):
        import_string("dummy.missing.DoesNotExist")
