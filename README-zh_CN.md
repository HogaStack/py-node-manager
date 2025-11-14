# py-node

一个方便在Python中使用Node.js的工具库。

[![Tests](https://github.com/HogaStack/py-node/workflows/Tests/badge.svg)](https://github.com/HogaStack/py-node/actions)
[![Coverage](https://codecov.io/gh/HogaStack/py-node/branch/main/graph/badge.svg)](https://codecov.io/gh/HogaStack/py-node)
[![GitHub](https://shields.io/badge/license-MIT-informational)](https://github.com/HogaStack/py-node/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/py-node.svg?color=dark-green)](https://pypi.org/project/py-node/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

简体中文 | [English](./README.md)

## 安装

```bash
pip install py-node
```

## 使用方法

### 基本用法

```python
from py_node import NodeManager

# 创建NodeManager实例
# download_node=True 表示如果系统中没有Node.js则自动下载
# node_version指定要下载的Node.js版本
manager = NodeManager(download_node=True, node_version='18.17.0')

# 获取Node.js、npm和npx的路径
node_path = manager.node_path  # 下载的Node.js路径，如果使用系统Node.js则为None
npm_path = manager.npm_path    # npm路径
npx_path = manager.npx_path    # npx路径

# 获取环境变量（如果使用下载的Node.js）
node_env = manager.node_env    # 环境变量字典
```

### 运行Node.js命令

```python
import subprocess
from py_node import NodeManager

manager = NodeManager(download_node=True, node_version='18.17.0')

# 运行Node.js命令
result = subprocess.run(
    [manager.npm_path, 'init', '-y'],
    env=manager.node_env,
    capture_output=True,
    text=True
)
print(result.stdout)
```

### 不自动下载Node.js

```python
from py_node import NodeManager

# 如果系统中没有Node.js将会抛出异常
manager = NodeManager(download_node=False, node_version='18.17.0')
```

## 测试

本项目使用pytest进行测试，测试覆盖率达到100%。

### 运行测试

在conda环境中运行测试：

```bash
# 激活conda环境
conda activate py-node

# 安装依赖
pip install -e .
pip install -r requirements-dev.txt

# 运行测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ --cov=py_node --cov-report=term-missing
```

### 测试结构

- `tests/test_node_manager.py` - NodeManager类的完整测试套件
- `tests/conftest.py` - pytest配置
- `tests/__init__.py` - 包初始化文件

所有代码路径都经过测试，包括：

- 正常执行路径
- 错误处理场景
- 平台特定行为
- CLI模式日志
- 缓存的Node.js使用
