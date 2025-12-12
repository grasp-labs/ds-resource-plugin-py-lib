# ds-resource-plugin-py-lib

A Python package from the ds-common library collection.

## Installation

Install the package using pip:

```bash
pip install ds-resource-plugin-py-lib
```

Or using uv (recommended):

```bash
uv pip install ds-resource-plugin-py-lib
```

## Quick Start

```python
from ds_resource_plugin_py_lib import __version__

print(f"ds-resource-plugin-py-lib version: {__version__}")
```

## Usage

```python
# Example usage
from ds_resource_plugin_py_lib.common.resource import ResourceClient

resource_client = ResourceClient()
linked_service = resource_client.linked_service(config=config)
dataset = resource_client.dataset(config=config)

linked_service.connect()

dataset.create()
dataset.read()
dataset.delete()
dataset.update()
dataset.rename()
```

## Requirements

- Python 3.11 or higher

## Documentation

Full documentation is available at:

- [GitHub Repository](https://github.com/grasp-labs/ds-resource-plugin-py-lib)
- [Documentation Site](https://grasp-labs.github.io/ds-resource-plugin-py-lib/)

## Development

To contribute or set up a development environment:

```bash
# Clone the repository
git clone https://github.com/grasp-labs/ds-resource-plugin-py-lib.git
cd ds-resource-plugin-py-lib

# Install development dependencies
uv sync --all-extras --dev

# Run tests
make test
```

See the
[README](https://github.com/grasp-labs/ds-resource-plugin-py-lib#readme)
for more information.

## License

This package is licensed under the Apache License 2.0. See the
[LICENSE-APACHE](https://github.com/grasp-labs/ds-resource-plugin-py-lib/blob/main/LICENSE-APACHE)
file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/grasp-labs/ds-resource-plugin-py-lib/issues)
- **Releases**: [GitHub Releases](https://github.com/grasp-labs/ds-resource-plugin-py-lib/releases)
