"""
Tests for the Joblet MCP Server
"""

import pytest

from joblet_mcp_server.server import JobletConfig, JobletMCPServer


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    return JobletConfig(
        rnx_binary_path="/usr/local/bin/rnx",
        config_file="/test/config.yaml",
        node_name="test-node",
    )


@pytest.fixture
def mcp_server(mock_config):
    """Create a JobletMCPServer instance"""
    return JobletMCPServer(mock_config)


class TestJobletMCPServer:
    """Test cases for JobletMCPServer"""

    def test_server_initialization(self, mcp_server, mock_config):
        """Test server initializes correctly"""
        assert mcp_server.config == mock_config
        assert mcp_server.server is not None

    def test_list_tools(self, mcp_server):
        """Test that server has basic structure"""
        # Test that the server can be instantiated and has expected methods
        assert hasattr(mcp_server, "_execute_tool")
        assert hasattr(mcp_server, "server")
        assert mcp_server.server is not None

    def test_config_defaults(self):
        """Test configuration defaults"""
        config = JobletConfig()
        assert config.rnx_binary_path == "rnx"
        assert config.config_file is None
        assert config.node_name == "default"
        assert config.json_output is True

    def test_config_custom_values(self):
        """Test configuration with custom values"""
        config = JobletConfig(
            rnx_binary_path="/custom/rnx",
            config_file="/custom/config.yaml",
            node_name="custom-node",
            json_output=False,
        )
        assert config.rnx_binary_path == "/custom/rnx"
        assert config.config_file == "/custom/config.yaml"
        assert config.node_name == "custom-node"
        assert config.json_output is False
