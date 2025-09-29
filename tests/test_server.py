"""
Tests for the Joblet MCP Server
"""

import json
from unittest.mock import AsyncMock, Mock, patch

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

    @pytest.mark.skip(
        reason="CLI server functionality is deprecated in favor of SDK-based server"
    )
    async def test_execute_tool_run_job(self, mcp_server):
        """Test executing run_job tool"""
        pass

    @pytest.mark.skip(
        reason="CLI server functionality is deprecated in favor of SDK-based server"
    )
    async def test_execute_tool_list_jobs(self, mcp_server):
        """Test executing list_jobs tool"""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = ("[]", "")
            mock_subprocess.return_value = mock_process

            result = await mcp_server._execute_tool("joblet_list_jobs", {})

            assert result == "[]"

    @pytest.mark.skip(
        reason="CLI server functionality is deprecated in favor of SDK-based server"
    )
    async def test_execute_tool_error_handling(self, mcp_server):
        """Test error handling in tool execution"""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = ("", "Error: Job not found")
            mock_subprocess.return_value = mock_process

            with pytest.raises(RuntimeError, match="Error: Job not found"):
                await mcp_server._execute_tool(
                    "joblet_get_job_status", {"job_uuid": "nonexistent"}
                )

    @pytest.mark.skip(
        reason="CLI server functionality is deprecated in favor of SDK-based server"
    )
    async def test_execute_tool_binary_not_found(self, mcp_server):
        """Test handling when rnx binary is not found"""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError()

            with pytest.raises(RuntimeError, match="rnx binary not found"):
                await mcp_server._execute_tool("joblet_list_jobs", {})

    @pytest.mark.skip(
        reason="CLI server functionality is deprecated in favor of SDK-based server"
    )
    async def test_execute_tool_unknown_tool(self, mcp_server):
        """Test handling unknown tool names"""
        with pytest.raises(ValueError, match="Unknown tool"):
            await mcp_server._execute_tool("unknown_tool", {})

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


@pytest.mark.skip(
    reason="CLI server functionality is deprecated in favor of SDK-based server"
)
class TestToolMappings:
    """Test tool name to command mappings"""

    @pytest.mark.parametrize(
        "tool_name,expected_cmd_start",
        [
            ("joblet_run_job", ["job", "run"]),
            ("joblet_list_jobs", ["job", "list"]),
            ("joblet_get_job_status", ["job", "status"]),
            ("joblet_get_job_logs", ["job", "log"]),
            ("joblet_stop_job", ["job", "stop"]),
            ("joblet_cancel_job", ["job", "cancel"]),
            ("joblet_delete_job", ["job", "delete"]),
            ("joblet_create_volume", ["volume", "create"]),
            ("joblet_list_volumes", ["volume", "list"]),
            ("joblet_remove_volume", ["volume", "remove"]),
            ("joblet_create_network", ["network", "create"]),
            ("joblet_list_networks", ["network", "list"]),
            ("joblet_remove_network", ["network", "remove"]),
            ("joblet_get_system_status", ["monitor", "status"]),
            ("joblet_get_system_metrics", ["monitor", "top"]),
            ("joblet_get_gpu_status", ["monitor", "gpu"]),
            ("joblet_list_nodes", ["nodes"]),
            ("joblet_list_runtimes", ["runtime", "list"]),
            ("joblet_remove_runtime", ["runtime", "remove"]),
        ],
    )
    @pytest.mark.asyncio
    async def test_tool_command_mapping(
        self, mcp_server, tool_name, expected_cmd_start
    ):
        """Test that tools map to correct rnx commands"""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = ("success", "")
            mock_subprocess.return_value = mock_process

            # Prepare minimal arguments for each tool
            args = {}
            if "uuid" in tool_name:
                args["job_uuid"] = "test-uuid"
            elif "workflow_uuid" in tool_name:
                args["workflow_uuid"] = "test-workflow-uuid"
            elif tool_name == "joblet_run_job":
                args["command"] = "echo"
            elif tool_name == "joblet_create_volume":
                args.update({"name": "test-vol", "size": "1GB"})
            elif tool_name == "joblet_create_network":
                args.update({"name": "test-net", "cidr": "10.0.1.0/24"})
            elif tool_name in ["joblet_remove_volume", "joblet_remove_network"]:
                args["name"] = "test-name"
            elif tool_name == "joblet_remove_runtime":
                args["runtime"] = "test-runtime"
            elif tool_name == "joblet_install_runtime":
                args["runtime_spec"] = "python:3.11"
            elif tool_name == "joblet_run_workflow":
                args["workflow_file"] = "test.yaml"

            await mcp_server._execute_tool(tool_name, args)

            # Get the command that was executed
            call_args = mock_subprocess.call_args[0][0]
            executed_cmd = list(call_args)

            # Check that the command starts with the expected parts
            # Skip the binary path and global flags, check the action part
            cmd_without_flags = []
            skip_next = False
            for i, part in enumerate(executed_cmd):
                if skip_next:
                    skip_next = False
                    continue
                if part in ["--config", "--node", "--json"]:
                    skip_next = True
                    continue
                if not part.startswith("-") and part != executed_cmd[0]:
                    cmd_without_flags.append(part)

            assert cmd_without_flags[: len(expected_cmd_start)] == expected_cmd_start
