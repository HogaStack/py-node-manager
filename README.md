# py-node

A tool library for conveniently using Node.js in Python.

[![Tests](https://github.com/HogaStack/py-node/workflows/Tests/badge.svg)](https://github.com/HogaStack/py-node/actions)
[![Coverage](https://codecov.io/gh/HogaStack/py-node/branch/main/graph/badge.svg)](https://codecov.io/gh/HogaStack/py-node)
[![GitHub](https://shields.io/badge/license-MIT-informational)](https://github.com/HogaStack/py-node/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/py-node.svg?color=dark-green)](https://pypi.org/project/py-node/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

English | [简体中文](./README-zh_CN.md)

## Installation

```bash
pip install py-node
```

## Usage

### Basic Usage

```python
from py_node import NodeManager

# Create NodeManager instance
# download_node=True means automatically download Node.js if not found in system
# node_version specifies the Node.js version to download
manager = NodeManager(download_node=True, node_version='18.17.0')

# Get paths to Node.js, npm, and npx
node_path = manager.node_path  # Path to downloaded Node.js, None if using system Node.js
npm_path = manager.npm_path    # Path to npm
npx_path = manager.npx_path    # Path to npx

# Get environment variables (if using downloaded Node.js)
node_env = manager.node_env    # Environment variables dictionary
```

### Running Node.js Commands

```python
import subprocess
from py_node import NodeManager

manager = NodeManager(download_node=True, node_version='18.17.0')

# Run Node.js commands
result = subprocess.run(
    [manager.npm_path, 'init', '-y'],
    env=manager.node_env,
    capture_output=True,
    text=True
)
print(result.stdout)
```

### Without Automatic Node.js Download

```python
from py_node import NodeManager

# Will raise an exception if Node.js is not found in the system
manager = NodeManager(download_node=False, node_version='18.17.0')
```

## Testing

This project uses pytest for testing with 100% code coverage.

### Running Tests

To run the tests in the conda environment:

```bash
# Activate the conda environment
conda activate py-node

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run tests with coverage report
pytest tests/ --cov=py_node --cov-report=term-missing
```

### Test Structure

- `tests/test_node_manager.py` - Complete test suite for NodeManager class
- `tests/conftest.py` - pytest configuration
- `tests/__init__.py` - Package initialization

All code paths are tested including:

- Normal execution paths
- Error handling scenarios
- Platform-specific behaviors
- CLI mode logging
- Cached Node.js usage
