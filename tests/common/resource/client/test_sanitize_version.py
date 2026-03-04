import pytest

from ds_resource_plugin_py_lib.libs.utils.sanitize import sanitize_version


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("v1.0.0", "1.0.0"),
        ("1.0.0", "1.0.0"),
        ("  v1.2.3  ", "1.2.3"),
        ("vv1.2.3", "1.2.3"),
        ("V1.2.3", "V1.2.3"),  # uppercase V is not stripped by current implementation
        ("", ""),
    ],
)
def test_sanitize_version(input_str: str, expected: str) -> None:
    assert sanitize_version(input_str) == expected
