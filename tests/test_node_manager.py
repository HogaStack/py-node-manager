import logging
import os
from unittest.mock import call, patch

import pytest

from py_node_manager.logger import ColoredFormatter
from py_node_manager.manager import NodeManager


@pytest.fixture
def mock_dependencies():
    """Fixture to mock common dependencies"""
    with patch('py_node_manager.manager.platform.system') as mock_system, patch(
        'py_node_manager.manager.platform.machine'
    ) as mock_machine, patch('py_node_manager.manager.os.path.dirname') as mock_dirname, patch(
        'py_node_manager.manager.os.path.abspath'
    ) as mock_abspath, patch('py_node_manager.manager.os.path.exists') as mock_exists, patch(
        'py_node_manager.manager.os.makedirs'
    ) as mock_makedirs, patch('py_node_manager.manager.os.chmod') as mock_chmod, patch(
        'py_node_manager.manager.os.remove'
    ) as mock_remove, patch('py_node_manager.manager.urllib.request.urlretrieve') as mock_urlretrieve, patch(
        'py_node_manager.manager.tarfile.open'
    ) as mock_tarfile, patch('py_node_manager.manager.zipfile.ZipFile') as mock_zipfile, patch(
        'py_node_manager.manager.logger'
    ) as mock_logger, patch('py_node_manager.manager.subprocess.run') as mock_subprocess, patch(
        'py_node_manager.manager.os.path.join', side_effect=os.path.join
    ) as mock_join:  # Keep real join behavior by default
        # Default setup
        mock_dirname.return_value = '/test/path'
        mock_abspath.return_value = '/test/path'
        mock_system.return_value = 'Linux'
        mock_machine.return_value = 'x86_64'

        yield {
            'system': mock_system,
            'machine': mock_machine,
            'dirname': mock_dirname,
            'abspath': mock_abspath,
            'exists': mock_exists,
            'makedirs': mock_makedirs,
            'chmod': mock_chmod,
            'remove': mock_remove,
            'urlretrieve': mock_urlretrieve,
            'tarfile': mock_tarfile,
            'zipfile': mock_zipfile,
            'logger': mock_logger,
            'subprocess': mock_subprocess,
            'join': mock_join,
        }


class TestNodeManager:
    """Test cases for NodeManager class"""

    @pytest.mark.parametrize('node_version', ['18.17.0', '20.10.0', '16.20.2'])
    def test_init_with_different_versions(self, node_version):
        """Test NodeManager initialization with different Node.js versions"""
        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=False, node_version=node_version)
            assert manager.download_node is False
            assert manager.node_version == node_version
            assert manager.is_cli is False

    def test_init(self):
        """Test NodeManager initialization"""
        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=False, node_version='18.17.0')
            assert manager.download_node is False
            assert manager.node_version == '18.17.0'
            assert manager.is_cli is False

    def test_init_with_cli(self):
        """Test NodeManager initialization with CLI flag"""
        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=True, node_version='18.17.0', is_cli=True)
            assert manager.download_node is True
            assert manager.node_version == '18.17.0'
            assert manager.is_cli is True

    def test_check_nodejs_available_success(self, mock_dependencies):
        """Test check_nodejs_available when Node.js is available"""
        mock_dependencies['subprocess'].return_value.returncode = 0
        mock_dependencies['subprocess'].return_value.stdout = 'v18.17.0\n'

        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=False, node_version='18.17.0')
            is_available, version = manager.check_nodejs_available()

            assert is_available is True
            assert version == 'v18.17.0'

    def test_check_nodejs_available_not_found(self, mock_dependencies):
        """Test check_nodejs_available when Node.js is not found"""
        mock_dependencies['subprocess'].side_effect = FileNotFoundError

        manager = NodeManager.__new__(NodeManager)  # Create instance without calling __init__
        is_available, version = manager.check_nodejs_available()

        assert is_available is False
        assert version == ''

    def test_check_nodejs_available_non_zero_return(self, mock_dependencies):
        """Test check_nodejs_available when Node.js command returns non-zero exit code"""
        mock_dependencies['subprocess'].return_value.returncode = 1

        manager = NodeManager.__new__(NodeManager)
        is_available, version = manager.check_nodejs_available()

        assert is_available is False
        assert version == ''

    @pytest.mark.parametrize('platform_name', ['Windows', 'Linux', 'Darwin'])
    def test_get_command_alias_by_platform(self, platform_name, mock_dependencies):
        """Test get_command_alias_by_platform on different platforms"""
        mock_dependencies['system'].return_value = platform_name

        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=False, node_version='18.17.0')
            result = manager.get_command_alias_by_platform('npm')

            if platform_name == 'Windows':
                assert result == 'npm.cmd'
            else:
                assert result == 'npm'

    @pytest.mark.parametrize(
        'platform_name,machine,expected_url',
        [
            ('Windows', 'AMD64', 'https://nodejs.org/dist/v18.17.0/node-v18.17.0-win-x64.zip'),
            ('Linux', 'aarch64', 'https://nodejs.org/dist/v18.17.0/node-v18.17.0-linux-arm64.tar.xz'),
            ('Linux', 'x86_64', 'https://nodejs.org/dist/v18.17.0/node-v18.17.0-linux-x64.tar.xz'),
            ('Darwin', 'arm64', 'https://nodejs.org/dist/v18.17.0/node-v18.17.0-darwin-arm64.tar.gz'),
            ('Darwin', 'x86_64', 'https://nodejs.org/dist/v18.17.0/node-v18.17.0-darwin-x64.tar.gz'),
        ],
    )
    def test_download_nodejs_url_generation(self, platform_name, machine, expected_url, mock_dependencies):
        """Test that download_nodejs generates correct URLs for different platforms"""
        mock_dependencies['system'].return_value = platform_name
        mock_dependencies['machine'].return_value = machine
        mock_dependencies['exists'].return_value = False

        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=True, node_version='18.17.0')

            try:
                manager.download_nodejs()
            except Exception:
                pass  # We're only interested in the URL generation

            mock_dependencies['urlretrieve'].assert_called_once()
            called_url = mock_dependencies['urlretrieve'].call_args[0][0]
            assert called_url == expected_url

    def test_download_nodejs_unsupported_platform(self, mock_dependencies):
        """Test download_nodejs with unsupported platform"""
        mock_dependencies['system'].return_value = 'UnsupportedOS'
        mock_dependencies['machine'].return_value = 'x86_64'

        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=True, node_version='18.17.0')

            with pytest.raises(RuntimeError) as excinfo:
                manager.download_nodejs()
            assert 'Unsupported platform: unsupportedos' in str(excinfo.value)

    def test_node_path_property(self):
        """Test _node_path property"""
        with patch.object(NodeManager, 'check_or_download_nodejs') as mock_check:
            mock_check.return_value = '/path/to/node'
            manager = NodeManager(download_node=True, node_version='18.17.0')
            assert manager.node_path == '/path/to/node'

    def test_node_env_property_with_node_path(self):
        """Test _node_env property when node_path is set"""
        with patch.object(NodeManager, 'check_or_download_nodejs', return_value='/path/to/node'):
            manager = NodeManager(download_node=True, node_version='18.17.0')

            with patch('py_node_manager.manager.os.environ.copy', return_value={'PATH': '/usr/bin'}), patch(
                'py_node_manager.manager.os.pathsep', ':'
            ):
                env = manager.node_env
                assert env is not None
                assert '/path/to' in env['PATH']

    def test_node_env_property_without_node_path(self):
        """Test _node_env property when node_path is None"""
        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=False, node_version='18.17.0')
            assert manager.node_env is None

    def test_npm_path_with_node_path(self, mock_dependencies):
        """Test _npm_path when node_path is set"""
        mock_dependencies['dirname'].return_value = '/path/to'
        mock_dependencies['exists'].return_value = True

        with patch.object(NodeManager, 'check_or_download_nodejs', return_value='/path/to/node'):
            manager = NodeManager(download_node=True, node_version='18.17.0')
            npm_path = manager.npm_path
            assert '/path/to' in npm_path

    def test_npx_path_with_node_path(self, mock_dependencies):
        """Test _npx_path when node_path is set"""
        mock_dependencies['dirname'].return_value = '/path/to'
        mock_dependencies['exists'].return_value = True

        with patch.object(NodeManager, 'check_or_download_nodejs', return_value='/path/to/node'):
            manager = NodeManager(download_node=True, node_version='18.17.0')
            npx_path = manager.npx_path
            assert '/path/to' in npx_path

    @pytest.mark.parametrize(
        'platform_name,expected_npm,expected_npx',
        [
            ('Windows', 'npm.cmd', 'npx.cmd'),
            ('Linux', 'npm', 'npx'),
            ('Darwin', 'npm', 'npx'),
        ],
    )
    def test_command_paths_without_node_path(self, platform_name, expected_npm, expected_npx, mock_dependencies):
        """Test command paths when node_path is None on different platforms"""
        mock_dependencies['system'].return_value = platform_name

        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=False, node_version='18.17.0')
            assert manager.npm_path == expected_npm
            assert manager.npx_path == expected_npx

    @pytest.mark.parametrize(
        'platform_name,machine,expected_node_dir',
        [
            ('Darwin', 'arm64', 'node-v18.17.0-darwin-arm64'),
            ('Darwin', 'x86_64', 'node-v18.17.0-darwin-x64'),
            ('Linux', 'aarch64', 'node-v18.17.0-linux-arm64'),
            ('Linux', 'x86_64', 'node-v18.17.0-linux-x64'),
            ('Windows', 'AMD64', 'node-v18.17.0-win-x64'),
        ],
    )
    def test_node_directory_name_generation(self, platform_name, machine, expected_node_dir, mock_dependencies):
        """Test that Node.js directory names are generated correctly for different platforms"""
        mock_dependencies['system'].return_value = platform_name
        mock_dependencies['machine'].return_value = machine
        mock_dependencies['exists'].return_value = False

        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=True, node_version='18.17.0')

            try:
                manager.download_nodejs()
            except Exception:
                pass

            # Construct the expected executable path based on platform
            # Note: os.path.join is real in our fixture for the most part
            base_path = os.path.join('/test/path', '.nodejs_cache', expected_node_dir)
            if platform_name == 'Windows':
                expected_executable = os.path.join(base_path, 'node.exe')
            else:
                expected_executable = os.path.join(base_path, 'bin', 'node')

            mock_dependencies['exists'].assert_any_call(expected_executable)

    def test_download_nodejs_cached_node(self, mock_dependencies):
        """Test download_nodejs when Node.js is already cached"""
        expected_node_dir = 'node-v18.17.0-linux-x64'
        expected_executable = f'/test/path/.nodejs_cache/{expected_node_dir}/bin/node'

        # Simulate that the node executable exists
        mock_dependencies['exists'].side_effect = lambda path: path == expected_executable

        with patch.object(NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = NodeManager(download_node=True, node_version='18.17.0')
            result = manager.download_nodejs()

            assert result == expected_executable
            mock_dependencies['logger'].info.assert_called_with(f'📦 Using cached Node.js from {expected_executable}')

    def test_download_nodejs_cli_mode_logs(self, mock_dependencies):
        """Test download_nodejs CLI mode logs"""
        expected_url = 'https://nodejs.org/dist/v18.17.0/node-v18.17.0-linux-x64.tar.xz'
        mock_dependencies['exists'].return_value = False

        manager = NodeManager.__new__(NodeManager)
        manager.download_node = True
        manager.node_version = '18.17.0'
        manager.is_cli = True
        manager.log_show_mode = 'all'

        try:
            manager.download_nodejs()
        except Exception:
            pass

        mock_dependencies['logger'].info.assert_any_call(f'📥 Downloading Node.js from {expected_url}...')
        mock_dependencies['logger'].info.assert_any_call('🔧 Extracting Node.js...')

    def test_check_or_download_nodejs_no_download_raises_error(self):
        """Test check_or_download_nodejs raises error when download_node=False and Node.js not found"""
        with patch.object(NodeManager, 'check_nodejs_available', return_value=(False, '')):
            manager = NodeManager.__new__(NodeManager)
            manager.download_node = False
            manager.node_version = '18.17.0'
            manager.is_cli = False

            with pytest.raises(RuntimeError) as excinfo:
                manager.check_or_download_nodejs()
            assert 'Node.js is required for offline mode but not found' in str(excinfo.value)

    def test_check_or_download_nodejs_no_download_cli_raises_error(self):
        """Test check_or_download_nodejs raises error when download_node=False and is_cli=True and Node.js not found"""
        with patch.object(NodeManager, 'check_nodejs_available', return_value=(False, '')):
            manager = NodeManager.__new__(NodeManager)
            manager.download_node = False
            manager.node_version = '18.17.0'
            manager.is_cli = True

            with pytest.raises(RuntimeError) as excinfo:
                manager.check_or_download_nodejs()
            assert 'Node.js is required but not found in PATH' in str(excinfo.value)

    def test_check_or_download_nodejs_returns_download_result(self):
        """Test check_or_download_nodejs returns the result of download_nodejs when Node.js is not found and download_node=True"""
        with patch.object(NodeManager, 'check_nodejs_available', return_value=(False, '')):
            manager = NodeManager.__new__(NodeManager)
            manager.download_node = True
            manager.node_version = '18.17.0'
            manager.is_cli = False

            expected_path = '/path/to/downloaded/node'
            with patch.object(manager, 'download_nodejs', return_value=expected_path):
                result = manager.check_or_download_nodejs()
                assert result == expected_path

    @pytest.mark.parametrize('mode', ['slim', 'hide'])
    def test_download_nodejs_log_show_mode(self, mode, mock_dependencies):
        """Test download_nodejs with different log_show_mode"""
        expected_url = 'https://nodejs.org/dist/v18.17.0/node-v18.17.0-linux-x64.tar.xz'
        mock_dependencies['exists'].return_value = False

        manager = NodeManager.__new__(NodeManager)
        manager.download_node = True
        manager.node_version = '18.17.0'
        manager.is_cli = True
        manager.log_show_mode = mode

        try:
            manager.download_nodejs()
        except Exception:
            pass

        download_msg = f'📥 Downloading Node.js from {expected_url}...'
        not_found_msg = '🌐 Node.js not found in PATH. Downloading Node.js...'
        # The exact path depends on how os.path.join works in the fixture, but we can rely on what we know
        node_dir = 'node-v18.17.0-linux-x64'
        expected_executable = os.path.join('/test/path', '.nodejs_cache', node_dir, 'bin', 'node')
        extracted_msg = f'✅ Node.js downloaded and extracted to {expected_executable}'

        if mode == 'slim':
            mock_dependencies['logger'].info.assert_any_call(not_found_msg)
            mock_dependencies['logger'].info.assert_any_call(extracted_msg)

            # Verify download_msg was NOT called
            # call_args_list is a list of call objects
            calls = mock_dependencies['logger'].info.call_args_list
            assert call(download_msg) not in calls

        elif mode == 'hide':
            mock_dependencies['logger'].info.assert_not_called()

    def test_use_system_nodejs_log_output(self, mock_dependencies):
        """Test using system Node.js with logging enabled"""
        # Configure subprocess mock to simulate installed Node.js
        mock_dependencies['subprocess'].return_value.returncode = 0
        mock_dependencies['subprocess'].return_value.stdout = 'v14.17.0\n'

        # Create instance manually to control properties directly
        manager = NodeManager.__new__(NodeManager)
        manager.download_node = False
        manager.node_version = '18.17.0'
        manager.is_cli = False
        manager.log_show_mode = 'all'

        # Call method directly
        result = manager.check_or_download_nodejs()

        assert result is None
        mock_dependencies['logger'].info.assert_called_with('💻 Using System Default Node.js v14.17.0')

    def test_check_nodejs_available_log_show_mode_hide(self, mock_dependencies):
        """Test check_nodejs_available with log_show_mode='hide'"""
        mock_dependencies['subprocess'].return_value.returncode = 0
        mock_dependencies['subprocess'].return_value.stdout = 'v18.17.0\n'

        manager = NodeManager.__new__(NodeManager)
        manager.download_node = False
        manager.node_version = '18.17.0'
        manager.is_cli = False
        manager.log_show_mode = 'hide'

        is_available, version = manager.check_nodejs_available()

        assert is_available is True
        assert version == 'v18.17.0'
        mock_dependencies['logger'].info.assert_not_called()

    @pytest.mark.parametrize('mode', ['slim', 'hide'])
    def test_download_nodejs_cached_node_log_mode(self, mode, mock_dependencies):
        """Test download_nodejs cached node with different log modes"""
        expected_node_dir = 'node-v18.17.0-linux-x64'
        expected_executable = f'/test/path/.nodejs_cache/{expected_node_dir}/bin/node'

        # Override exists to find the cached node
        mock_dependencies['exists'].side_effect = lambda path: path == expected_executable

        manager = NodeManager.__new__(NodeManager)
        manager.download_node = True
        manager.node_version = '18.17.0'
        manager.is_cli = True
        manager.log_show_mode = mode

        result = manager.download_nodejs()

        assert result == expected_executable
        msg = f'📦 Using cached Node.js from {expected_executable}'

        if mode == 'slim':
            mock_dependencies['logger'].info.assert_called_with(msg)
        elif mode == 'hide':
            mock_dependencies['logger'].info.assert_not_called()


def test_logger_formatter():
    """Test ColoredFormatter"""
    formatter = ColoredFormatter('%(levelname)s: %(message)s')
    record = logging.LogRecord(
        name='test', level=logging.INFO, pathname='test.py', lineno=10, msg='test message', args=(), exc_info=None
    )
    record.funcName = 'test_func'

    formatted = formatter.format(record)

    # Check for color codes
    assert '\033[32mINFO\033[0m' in formatted  # Green for INFO
    assert 'test message' in formatted

    # Test other levels
    # Create new record to avoid side effects from previous formatting

    record_error = logging.LogRecord(
        name='test', level=logging.ERROR, pathname='test.py', lineno=10, msg='error message', args=(), exc_info=None
    )
    record_error.funcName = 'test_func'
    formatted = formatter.format(record_error)
    assert '\033[31mERROR\033[0m' in formatted  # Red for ERROR

    record_debug = logging.LogRecord(
        name='test', level=logging.DEBUG, pathname='test.py', lineno=10, msg='debug message', args=(), exc_info=None
    )
    record_debug.funcName = 'test_func'
    formatted = formatter.format(record_debug)
    assert '\033[36mDEBUG\033[0m' in formatted  # Cyan for DEBUG
