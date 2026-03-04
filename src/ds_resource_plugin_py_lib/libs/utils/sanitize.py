"""
**File:** ``sanitize.py``
**Region:** ``ds_resource_plugin_py_lib/libs/utils``

Description
-----------
Utility function to sanitize version strings to ensure consistent formatting.

Example
-------
.. code-block:: python

    from ds_resource_plugin_py_lib.libs.utils.sanitize import sanitize_version

    # Sanitize a version string.
    version = sanitize_version("  v1.2.3  ")
    result = version  # Returns '1.2.3'
"""


def sanitize_version(version: str) -> str:
    """
    Sanitize version string to ensure it follows a consistent format.
    We can receive versions written as semver (v1.0.0)
    or just the number (1.0.0). This function will strip any leading 'v' and whitespace.

    Args:
        version: The version string to sanitize.

    Returns:
        A sanitized version string.
    """
    # First remove surrounding whitespace, then strip any leading lowercase 'v'.
    # Order matters because inputs like '  v1.2.3  ' should become '1.2.3'.
    return version.strip().lstrip("v").strip()
