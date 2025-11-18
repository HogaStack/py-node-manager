import logging
import os
import platform
import subprocess
import tarfile
import urllib.request
import zipfile
from typing import Dict, Optional, Tuple
from .logger import get_logger


logger = get_logger(logging.getLogger(__name__))


class NodeManager:
    """
    Node.js manager class
    """

    def __init__(self, download_node: bool, node_version: str, is_cli: bool = False):
        """
        Node.js manager class

        Args:
            download_node (bool): Whether to download Node.js if not found
            node_version (str): Node.js version to download if download_node is True
            is_cli (bool): Whether this is being called from CLI (affects error messages)
        """
        self.download_node = download_node
        self.node_version = node_version
        self.is_cli = is_cli
        self.node_path = self._node_path()
        self.node_env = self._node_env()
        self.npm_path = self._npm_path()
        self.npx_path = self._npx_path()

    def check_nodejs_available(self) -> Tuple[bool, str]:
        """
        Check if Node.js is available in PATH

        Returns:
            Tuple[bool, str]: A tuple containing:
                - bool: True if Node.js is available, False otherwise
                - str: The version of Node.js if available, empty string otherwise
        """
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout.strip()
        except FileNotFoundError:
            pass

        return False, ''

    def download_nodejs(self) -> str:
        """
        Download Node.js for the current platform

        Returns:
            str: Path to downloaded Node.js executable
        """
        # Determine platform
        system = platform.system().lower()
        machine = platform.machine().lower()

        # Define download URLs for different platforms
        if system == 'darwin':  # macOS
            if machine == 'arm64' or machine == 'aarch64':
                node_url = f'https://nodejs.org/dist/v{self.node_version}/node-v{self.node_version}-darwin-arm64.tar.gz'
                node_dir = f'node-v{self.node_version}-darwin-arm64'
            else:
                node_url = f'https://nodejs.org/dist/v{self.node_version}/node-v{self.node_version}-darwin-x64.tar.gz'
                node_dir = f'node-v{self.node_version}-darwin-x64'
        elif system == 'linux':
            if machine == 'aarch64':
                node_url = f'https://nodejs.org/dist/v{self.node_version}/node-v{self.node_version}-linux-arm64.tar.xz'
                node_dir = f'node-v{self.node_version}-linux-arm64'
            else:
                node_url = f'https://nodejs.org/dist/v{self.node_version}/node-v{self.node_version}-linux-x64.tar.xz'
                node_dir = f'node-v{self.node_version}-linux-x64'
        elif system == 'windows':
            node_url = f'https://nodejs.org/dist/v{self.node_version}/node-v{self.node_version}-win-x64.zip'
            node_dir = f'node-v{self.node_version}-win-x64'
        else:
            raise RuntimeError(f'Unsupported platform: {system}')

        # Create directory for downloaded Node.js within the package directory
        # Use the package directory instead of current working directory
        # Get the directory of this utils.py file
        package_dir = os.path.dirname(os.path.abspath(__file__))
        node_dir_path = os.path.join(package_dir, '.nodejs_cache')
        if not os.path.exists(node_dir_path):
            os.makedirs(node_dir_path)

        # Check if Node.js is already downloaded
        if system == 'windows':
            node_executable = os.path.join(node_dir_path, node_dir, 'node.exe')
        else:
            node_executable = os.path.join(node_dir_path, node_dir, 'bin', 'node')

        # If Node.js already exists, return the path without downloading
        if os.path.exists(node_executable):
            logger.info(f'📦 Using cached Node.js from {node_executable}')
            return node_executable

        # Download Node.js
        node_archive = os.path.join(node_dir_path, os.path.basename(node_url))
        logger.info('🌐 Node.js not found in PATH. Downloading Node.js...')
        if self.is_cli:
            logger.info(f'📥 Downloading Node.js from {node_url}...')
        urllib.request.urlretrieve(node_url, node_archive)

        # Extract Node.js
        if self.is_cli:
            logger.info('🔧 Extracting Node.js...')
        if node_archive.endswith('.tar.gz'):
            with tarfile.open(node_archive, 'r:gz') as tar:
                tar.extractall(node_dir_path)
        elif node_archive.endswith('.tar.xz'):
            with tarfile.open(node_archive, 'r:xz') as tar:
                tar.extractall(node_dir_path)
        elif node_archive.endswith('.zip'):
            with zipfile.ZipFile(node_archive, 'r') as zip_ref:
                zip_ref.extractall(node_dir_path)

        # Remove archive
        os.remove(node_archive)

        # Make executable if not on Windows
        if system != 'windows':
            os.chmod(node_executable, 0o755)

        logger.info(f'✅ Node.js downloaded and extracted to {node_executable}')
        return node_executable

    def check_or_download_nodejs(self) -> Optional[str]:
        """
        Check if Node.js is available or download it if requested

        Returns:
            Optional[str]: Path to Node.js executable or None if using system Node.js
        """
        # First check if Node.js is available in PATH
        is_available, version = self.check_nodejs_available()
        if is_available:
            logger.info(f'💻 Using System Default Node.js {version}')

            return None  # Use system Node.js

        # If not found and download is not requested, raise error
        if not self.download_node:
            if self.is_cli:
                raise RuntimeError(
                    'Node.js is required but not found in PATH. '
                    'Install Node.js or use --download-node to automatically download it.'
                )
            else:
                raise RuntimeError(
                    'Node.js is required for offline mode but not found. '
                    'Install Node.js or use download_node=True to automatically download it.'
                )

        # Download Node.js using the shared utility function
        return self.download_nodejs()

    def get_command_alias_by_platform(self, command: str) -> str:
        """
        Get the command alias for a given command on the current platform.

        Args:
            command (str): Command to get alias for
        Returns:
            str: Command alias
        """
        if platform.system().lower() == 'windows':
            return command + '.cmd'
        else:
            return command

    def _node_path(self) -> Optional[str]:
        """
        Get the path to the Node.js executable

        Returns:
            Optional[str]: Path to Node.js executable or None if using system Node.js
        """
        node_path = self.check_or_download_nodejs()

        return node_path

    def _node_env(self) -> Optional[Dict[str, str]]:
        """
        Get the environment variables for the Node.js executable

        Returns:
            Optional[Dict[str, str]]: Environment variables for Node.js executable or None if using system Node.js
        """
        env = None
        if self.node_path:
            node_dir = os.path.dirname(self.node_path)
            env = os.environ.copy()
            env['PATH'] = node_dir + os.pathsep + env.get('PATH', '')

        return env

    def _npm_path(self) -> str:
        """
        Get the path to the npm executable

        Returns:
            str: Path to npm executable
        """
        if self.node_path:
            # When using downloaded Node.js, we need to use npm from the same directory
            node_dir = os.path.dirname(self.node_path)
            npm_path = os.path.join(node_dir, self.get_command_alias_by_platform('npm'))
            # If npm doesn't exist in the same directory, check in bin subdirectory
            if not os.path.exists(npm_path):
                npm_path = os.path.join(node_dir, 'bin', self.get_command_alias_by_platform('npm'))

        else:
            npm_path = self.get_command_alias_by_platform('npm')

        return npm_path

    def _npx_path(self) -> str:
        """
        Get the path to the npx executable

        Returns:
            str: Path to npx executable
        """
        if self.node_path:
            # When using downloaded Node.js, we need to use npx from the same directory
            node_dir = os.path.dirname(self.node_path)
            npx_path = os.path.join(node_dir, self.get_command_alias_by_platform('npx'))
            # If npx doesn't exist in the same directory, check in bin subdirectory
            if not os.path.exists(npx_path):
                npx_path = os.path.join(node_dir, 'bin', self.get_command_alias_by_platform('npx'))

        else:
            npx_path = self.get_command_alias_by_platform('npx')

        return npx_path
