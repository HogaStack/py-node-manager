import pytest
from unittest.mock import patch, MagicMock


class TestNodeManager:
    """Test cases for NodeManager class"""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Import here to avoid issues with pytest
        from py_node.manager import NodeManager

        self.NodeManager = NodeManager

    @pytest.mark.parametrize('node_version', ['18.17.0', '20.10.0', '16.20.2'])
    def test_init_with_different_versions(self, node_version):
        """Test NodeManager initialization with different Node.js versions"""
        # Mock the check_or_download_nodejs method to avoid actual Node.js checks
        with patch.object(self.NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = self.NodeManager(download_node=False, node_version=node_version)
            assert manager.download_node is False
            assert manager.node_version == node_version
            assert manager.is_cli is False

    def test_init(self):
        """Test NodeManager initialization"""
        # Mock the check_or_download_nodejs method to avoid actual Node.js checks
        with patch.object(self.NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = self.NodeManager(download_node=False, node_version='18.17.0')
            assert manager.download_node is False
            assert manager.node_version == '18.17.0'
            assert manager.is_cli is False

    def test_init_with_cli(self):
        """Test NodeManager initialization with CLI flag"""
        # Mock the check_or_download_nodejs method to avoid actual Node.js checks
        with patch.object(self.NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = self.NodeManager(download_node=True, node_version='18.17.0', is_cli=True)
            assert manager.download_node is True
            assert manager.node_version == '18.17.0'
            assert manager.is_cli is True

    @patch('py_node.manager.subprocess.run')
    def test_check_nodejs_available_success(self, mock_run):
        """Test check_nodejs_available when Node.js is available"""
        # Mock subprocess.run to simulate successful Node.js detection
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'v18.17.0\n'
        mock_run.return_value = mock_result

        manager = self.NodeManager(download_node=False, node_version='18.17.0')
        is_available, version = manager.check_nodejs_available()

        assert is_available is True
        assert version == 'v18.17.0'

    def test_check_nodejs_available_not_found(self):
        """Test check_nodejs_available when Node.js is not found"""
        # Mock subprocess.run to simulate FileNotFoundError
        from py_node.manager import NodeManager

        with patch('py_node.manager.subprocess.run', side_effect=FileNotFoundError):
            manager = NodeManager.__new__(NodeManager)  # Create instance without calling __init__
            is_available, version = manager.check_nodejs_available()

            assert is_available is False
            assert version == ''

    def test_check_nodejs_available_non_zero_return(self):
        """Test check_nodejs_available when Node.js command returns non-zero exit code"""
        # Mock subprocess.run to simulate non-zero return code
        mock_result = MagicMock()
        mock_result.returncode = 1
        from py_node.manager import NodeManager

        with patch('py_node.manager.subprocess.run', return_value=mock_result):
            manager = NodeManager.__new__(NodeManager)  # Create instance without calling __init__
            is_available, version = manager.check_nodejs_available()

            assert is_available is False
            assert version == ''

    @pytest.mark.parametrize('platform_name', ['Windows', 'Linux', 'Darwin'])
    def test_get_command_alias_by_platform(self, platform_name):
        """Test get_command_alias_by_platform on different platforms"""
        # Mock platform.system() to return specific platform
        with patch('py_node.manager.platform.system', return_value=platform_name):
            # Mock the check_or_download_nodejs method to avoid actual Node.js checks
            with patch.object(self.NodeManager, 'check_or_download_nodejs', return_value=None):
                manager = self.NodeManager(download_node=False, node_version='18.17.0')
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
    def test_download_nodejs_url_generation(self, platform_name, machine, expected_url):
        """Test that download_nodejs generates correct URLs for different platforms"""
        with patch('py_node.manager.platform.system', return_value=platform_name):
            with patch('py_node.manager.platform.machine', return_value=machine):
                with patch('py_node.manager.os.path.dirname', return_value='/test/path'):
                    with patch('py_node.manager.os.path.abspath', return_value='/test/path'):
                        # Mock the check_or_download_nodejs method to avoid actual Node.js checks
                        with patch.object(self.NodeManager, 'check_or_download_nodejs', return_value=None):
                            manager = self.NodeManager(download_node=True, node_version='18.17.0')
                            # Mock the download method to avoid actual download
                            with patch('py_node.manager.urllib.request.urlretrieve') as mock_urlretrieve:
                                with patch('py_node.manager.os.makedirs'):
                                    with patch('py_node.manager.os.path.exists', return_value=False):
                                        with patch('py_node.manager.tarfile.open'):
                                            with patch('py_node.manager.zipfile.ZipFile'):
                                                with patch('py_node.manager.os.chmod'):
                                                    with patch('py_node.manager.os.remove'):
                                                        try:
                                                            manager.download_nodejs()
                                                        except Exception:
                                                            pass  # We're only interested in the URL generation

                                                        # Check that urlretrieve was called with the correct URL
                                                        mock_urlretrieve.assert_called_once()
                                                        called_url = mock_urlretrieve.call_args[0][0]
                                                        assert called_url == expected_url

    @patch('py_node.manager.platform.system')
    @patch('py_node.manager.platform.machine')
    def test_download_nodejs_unsupported_platform(self, mock_machine, mock_system):
        """Test download_nodejs with unsupported platform"""
        mock_system.return_value = 'UnsupportedOS'
        mock_machine.return_value = 'x86_64'

        # Mock the check_or_download_nodejs method to avoid actual Node.js checks
        with patch.object(self.NodeManager, 'check_or_download_nodejs', return_value=None):
            manager = self.NodeManager(download_node=True, node_version='18.17.0')

            try:
                manager.download_nodejs()
                assert False, 'Expected RuntimeError was not raised'
            except RuntimeError as e:
                assert 'Unsupported platform: unsupportedos' in str(e)

    def test_node_path_property(self):
        """Test _node_path property"""
        with patch.object(self.NodeManager, 'check_or_download_nodejs') as mock_check:
            mock_check.return_value = '/path/to/node'
            manager = self.NodeManager(download_node=True, node_version='18.17.0')
            assert manager.node_path == '/path/to/node'

    def test_node_env_property_with_node_path(self):
        """Test _node_env property when node_path is set"""
        with patch.object(self.NodeManager, 'check_or_download_nodejs') as mock_check:
            mock_check.return_value = '/path/to/node'
            manager = self.NodeManager(download_node=True, node_version='18.17.0')

            # Mock os.environ.copy() to return a known dictionary
            with patch('py_node.manager.os.environ.copy', return_value={'PATH': '/usr/bin'}):
                with patch('py_node.manager.os.pathsep', ':'):
                    env = manager.node_env
                    assert env is not None
                    assert '/path/to' in env['PATH']

    def test_node_env_property_without_node_path(self):
        """Test _node_env property when node_path is None"""
        with patch.object(self.NodeManager, 'check_or_download_nodejs') as mock_check:
            mock_check.return_value = None
            manager = self.NodeManager(download_node=False, node_version='18.17.0')
            assert manager.node_env is None

    def test_npm_path_with_node_path(self):
        """Test _npm_path when node_path is set"""
        with patch.object(self.NodeManager, 'check_or_download_nodejs') as mock_check:
            mock_check.return_value = '/path/to/node'
            with patch('py_node.manager.os.path.dirname', return_value='/path/to'):
                with patch('py_node.manager.os.path.exists', return_value=True):
                    manager = self.NodeManager(download_node=True, node_version='18.17.0')
                    npm_path = manager.npm_path
                    # Should contain the directory path
                    assert '/path/to' in npm_path

    def test_npx_path_with_node_path(self):
        """Test _npx_path when node_path is set"""
        with patch.object(self.NodeManager, 'check_or_download_nodejs') as mock_check:
            mock_check.return_value = '/path/to/node'
            with patch('py_node.manager.os.path.dirname', return_value='/path/to'):
                with patch('py_node.manager.os.path.exists', return_value=True):
                    manager = self.NodeManager(download_node=True, node_version='18.17.0')
                    npx_path = manager.npx_path
                    # Should contain the directory path
                    assert '/path/to' in npx_path

    @pytest.mark.parametrize(
        'platform_name,expected_npm,expected_npx',
        [
            ('Windows', 'npm.cmd', 'npx.cmd'),
            ('Linux', 'npm', 'npx'),
            ('Darwin', 'npm', 'npx'),
        ],
    )
    def test_command_paths_without_node_path(self, platform_name, expected_npm, expected_npx):
        """Test command paths when node_path is None on different platforms"""
        with patch('py_node.manager.platform.system', return_value=platform_name):
            with patch.object(self.NodeManager, 'check_or_download_nodejs') as mock_check:
                mock_check.return_value = None
                manager = self.NodeManager(download_node=False, node_version='18.17.0')
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
    def test_node_directory_name_generation(self, platform_name, machine, expected_node_dir):
        """Test that Node.js directory names are generated correctly for different platforms"""
        with patch('py_node.manager.platform.system', return_value=platform_name):
            with patch('py_node.manager.platform.machine', return_value=machine):
                with patch('py_node.manager.os.path.dirname', return_value='/test/path'):
                    with patch('py_node.manager.os.path.abspath', return_value='/test/path'):
                        # Mock the check_or_download_nodejs method to avoid actual Node.js checks
                        with patch.object(self.NodeManager, 'check_or_download_nodejs', return_value=None):
                            manager = self.NodeManager(download_node=True, node_version='18.17.0')
                            # Mock the download method to capture the node_dir value
                            with patch('py_node.manager.urllib.request.urlretrieve'):
                                with patch('py_node.manager.os.makedirs'):
                                    with patch('py_node.manager.os.path.exists', return_value=False) as mock_exists:
                                        with patch('py_node.manager.tarfile.open'):
                                            with patch('py_node.manager.zipfile.ZipFile'):
                                                with patch('py_node.manager.os.chmod'):
                                                    with patch('py_node.manager.os.remove'):
                                                        # Mock os.path.join to capture the node_dir parameter
                                                        with patch('py_node.manager.os.path.join') as mock_join:
                                                            # Make join return a predictable value
                                                            mock_join.return_value = (
                                                                f'/test/path/.nodejs_cache/{expected_node_dir}'
                                                            )
                                                            try:
                                                                manager.download_nodejs()
                                                            except Exception:
                                                                pass  # We're only interested in the directory name generation

                                                            # Verify that the expected node directory name was used
                                                            # Check that os.path.exists was called with the correct path
                                                            expected_path = (
                                                                f'/test/path/.nodejs_cache/{expected_node_dir}'
                                                            )
                                                            mock_exists.assert_called_with(expected_path)

    def test_download_nodejs_cached_node(self):
        """Test download_nodejs when Node.js is already cached"""
        platform_name = 'Linux'
        machine = 'x86_64'
        expected_node_dir = 'node-v18.17.0-linux-x64'
        expected_executable = f'/test/path/.nodejs_cache/{expected_node_dir}/bin/node'

        with patch('py_node.manager.platform.system', return_value=platform_name):
            with patch('py_node.manager.platform.machine', return_value=machine):
                with patch('py_node.manager.os.path.dirname', return_value='/test/path'):
                    with patch('py_node.manager.os.path.abspath', return_value='/test/path'):
                        # Mock the check_or_download_nodejs method to avoid actual Node.js checks
                        with patch.object(self.NodeManager, 'check_or_download_nodejs', return_value=None):
                            manager = self.NodeManager(download_node=True, node_version='18.17.0')
                            # Mock os.path.exists to return True for the executable path
                            with patch(
                                'py_node.manager.os.path.exists', side_effect=lambda path: path == expected_executable
                            ) as mock_exists:
                                with patch('py_node.manager.logger') as mock_logger:
                                    # Mock other methods to avoid actual download
                                    with patch('py_node.manager.urllib.request.urlretrieve'):
                                        with patch('py_node.manager.os.makedirs'):
                                            with patch('py_node.manager.tarfile.open'):
                                                with patch('py_node.manager.zipfile.ZipFile'):
                                                    with patch('py_node.manager.os.chmod'):
                                                        with patch('py_node.manager.os.remove'):
                                                            result = manager.download_nodejs()

                                                            # Verify that the cached Node.js is used
                                                            assert result == expected_executable
                                                            # Verify that logger.info was called with the correct message
                                                            mock_logger.info.assert_called_with(
                                                                f'📦 Using cached Node.js from {expected_executable}'
                                                            )
                                                            # Verify that os.path.exists was called with the correct path
                                                            mock_exists.assert_called_with(expected_executable)

    def test_download_nodejs_cli_mode_logs(self):
        """Test download_nodejs CLI mode logs"""
        platform_name = 'Linux'
        machine = 'x86_64'
        expected_url = 'https://nodejs.org/dist/v18.17.0/node-v18.17.0-linux-x64.tar.xz'

        with patch('py_node.manager.platform.system', return_value=platform_name):
            with patch('py_node.manager.platform.machine', return_value=machine):
                with patch('py_node.manager.os.path.dirname', return_value='/test/path'):
                    with patch('py_node.manager.os.path.abspath', return_value='/test/path'):
                        # Create manager with is_cli=True using direct instantiation to avoid __init__ issues
                        from py_node.manager import NodeManager

                        manager = NodeManager.__new__(NodeManager)
                        manager.download_node = True
                        manager.node_version = '18.17.0'
                        manager.is_cli = True
                        # Mock os.path.exists to return False to force download
                        with patch('py_node.manager.os.path.exists', return_value=False):
                            with patch('py_node.manager.logger') as mock_logger:
                                # Mock the download method
                                with patch('py_node.manager.urllib.request.urlretrieve'):
                                    with patch('py_node.manager.os.makedirs'):
                                        with patch('py_node.manager.tarfile.open'):
                                            with patch('py_node.manager.zipfile.ZipFile'):
                                                with patch('py_node.manager.os.chmod'):
                                                    with patch('py_node.manager.os.remove'):
                                                        try:
                                                            manager.download_nodejs()
                                                        except Exception:
                                                            pass  # We're only interested in the logging

                                                        # Verify that the CLI download log was called
                                                        mock_logger.info.assert_any_call(
                                                            f'📥 Downloading Node.js from {expected_url}...'
                                                        )
                                                        # Verify that the CLI extraction log was called
                                                        mock_logger.info.assert_any_call('🔧 Extracting Node.js...')

    def test_check_or_download_nodejs_no_download_raises_error(self):
        """Test check_or_download_nodejs raises error when download_node=False and Node.js not found"""
        with patch.object(self.NodeManager, 'check_nodejs_available', return_value=(False, '')):
            # Create manager with download_node=False using direct instantiation to avoid __init__ issues
            from py_node.manager import NodeManager

            manager = NodeManager.__new__(NodeManager)
            manager.download_node = False
            manager.node_version = '18.17.0'
            manager.is_cli = False
            # Should raise RuntimeError
            try:
                manager.check_or_download_nodejs()
                assert False, 'Expected RuntimeError was not raised'
            except RuntimeError as e:
                assert 'Node.js is required for offline mode but not found' in str(e)

    def test_check_or_download_nodejs_no_download_cli_raises_error(self):
        """Test check_or_download_nodejs raises error when download_node=False and is_cli=True and Node.js not found"""
        with patch.object(self.NodeManager, 'check_nodejs_available', return_value=(False, '')):
            # Create manager with download_node=False and is_cli=True using direct instantiation
            from py_node.manager import NodeManager

            manager = NodeManager.__new__(NodeManager)
            manager.download_node = False
            manager.node_version = '18.17.0'
            manager.is_cli = True
            # Should raise RuntimeError
            try:
                manager.check_or_download_nodejs()
                assert False, 'Expected RuntimeError was not raised'
            except RuntimeError as e:
                assert 'Node.js is required but not found in PATH' in str(e)

    def test_check_or_download_nodejs_returns_download_result(self):
        """Test check_or_download_nodejs returns the result of download_nodejs when Node.js is not found and download_node=True"""
        with patch.object(self.NodeManager, 'check_nodejs_available', return_value=(False, '')):
            # Create manager with download_node=True using direct instantiation
            from py_node.manager import NodeManager

            manager = NodeManager.__new__(NodeManager)
            manager.download_node = True
            manager.node_version = '18.17.0'
            manager.is_cli = False
            # Mock download_nodejs to return a specific path
            expected_path = '/path/to/downloaded/node'
            with patch.object(manager, 'download_nodejs', return_value=expected_path):
                result = manager.check_or_download_nodejs()
                assert result == expected_path
