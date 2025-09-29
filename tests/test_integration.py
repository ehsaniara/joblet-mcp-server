"""
Integration tests for Joblet MCP Server

These tests require a working rnx installation and Joblet server connection.
They can be skipped if the environment is not available.
"""

import asyncio
import shutil
from unittest.mock import patch

import pytest

from joblet_mcp_server.server import JobletConfig, JobletMCPServer


class TestIntegration:
    """Integration tests that require actual rnx binary"""

    @pytest.fixture
    def skip_if_no_rnx(self):
        """Skip tests if rnx binary is not available"""
        if not shutil.which("rnx"):
            pytest.skip("rnx binary not found - skipping integration tests")

    @pytest.fixture
    def integration_config(self):
        """Create config for integration tests"""
        return JobletConfig(
            rnx_binary_path="rnx",
            config_file=None,  # Use default config discovery
            node_name="default",
        )

    @pytest.fixture
    def integration_server(self, integration_config):
        """Create server for integration tests"""
        return JobletMCPServer(integration_config)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rnx_version(self, integration_server, skip_if_no_rnx):
        """Test that we can execute rnx --version"""
        # This is a basic test to verify rnx is working
        try:
            process = await asyncio.create_subprocess_exec(
                "rnx",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True,
            )
            stdout, stderr = await process.communicate()

            # Should exit successfully and have version info
            assert process.returncode == 0
            assert "rnx" in stdout.lower() or "version" in stdout.lower()

        except Exception as e:
            pytest.skip(f"rnx not working properly: {e}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_nodes_command(self, integration_server, skip_if_no_rnx):
        """Test listing nodes (should work even without server connection)"""
        try:
            result = await integration_server._execute_tool("joblet_list_nodes", {})
            # Even if no config exists, this should return some output or a helpful error
            assert isinstance(result, str)

        except RuntimeError as e:
            # Expected if no config is set up
            assert "config" in str(e).lower() or "connection" in str(e).lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_help_command(self, integration_server, skip_if_no_rnx):
        """Test that rnx help works (doesn't require server connection)"""
        # This bypasses our tool system to test raw rnx execution
        try:
            process = await asyncio.create_subprocess_exec(
                "rnx",
                "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True,
            )
            stdout, stderr = await process.communicate()

            assert process.returncode == 0
            assert "usage" in stdout.lower() or "commands" in stdout.lower()

        except Exception as e:
            pytest.skip(f"rnx help failed: {e}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_with_invalid_args(self, integration_server, skip_if_no_rnx):
        """Test error handling with invalid arguments"""
        with pytest.raises(RuntimeError):
            # This should fail because the job UUID doesn't exist
            await integration_server._execute_tool(
                "joblet_get_job_status", {"job_uuid": "nonexistent-job-uuid"}
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_command_building(self, integration_server, skip_if_no_rnx):
        """Test that commands are built correctly"""
        # Mock the subprocess execution to see what command would be run
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = type(
                "MockProcess",
                (),
                {"returncode": 0, "communicate": lambda: asyncio.create_future()},
            )()
            mock_process.communicate().set_result(('{"success": true}', ""))
            mock_subprocess.return_value = mock_process

            await integration_server._execute_tool(
                "joblet_run_job", {"command": "echo", "args": ["hello"], "max_cpu": 50}
            )

            # Check that the command was built correctly
            call_args = mock_subprocess.call_args[0][0]

            # Should contain the expected parts
            assert any("rnx" in str(arg) for arg in call_args)
            assert "job" in call_args
            assert "run" in call_args
            assert "echo" in call_args
            assert "hello" in call_args
            assert "--max-cpu" in call_args
            assert "50" in call_args

    def test_config_validation(self):
        """Test that configuration validation works"""
        # Valid config
        config = JobletConfig(
            rnx_binary_path="/usr/local/bin/rnx",
            config_file="/path/to/config.yaml",
            node_name="test-node",
        )
        assert config.rnx_binary_path == "/usr/local/bin/rnx"
        assert config.config_file == "/path/to/config.yaml"
        assert config.node_name == "test-node"

        # Default config
        default_config = JobletConfig()
        assert default_config.rnx_binary_path == "rnx"
        assert default_config.config_file is None
        assert default_config.node_name == "default"
        assert default_config.json_output is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_schema_validation(self, integration_server):
        """Test that our tool schemas match what rnx expects"""
        # Get the list of tools
        handler = None
        for h in integration_server.server._list_tools_handlers:
            handler = h
            break

        assert handler is not None
        tools = await handler()

        # Check that key tools exist and have required properties
        tool_names = [tool.name for tool in tools]

        required_tools = [
            "joblet_run_job",
            "joblet_list_jobs",
            "joblet_get_job_status",
            "joblet_get_system_status",
            "joblet_create_volume",
            "joblet_list_nodes",
        ]

        for required_tool in required_tools:
            assert required_tool in tool_names

        # Check that joblet_run_job has the expected schema
        run_job_tool = next(tool for tool in tools if tool.name == "joblet_run_job")
        schema = run_job_tool.inputSchema

        assert "command" in schema["required"]
        assert "command" in schema["properties"]
        assert schema["properties"]["command"]["type"] == "string"


class TestMockIntegration:
    """Integration-style tests that use mocking to avoid requiring real servers"""

    @pytest.fixture
    def mock_server(self):
        """Create a server with mocked configuration"""
        config = JobletConfig(
            rnx_binary_path="/mock/rnx",
            config_file="/mock/config.yaml",
            node_name="mock-node",
        )
        return JobletMCPServer(config)

    @pytest.mark.asyncio
    async def test_full_job_lifecycle_mock(self, mock_server):
        """Test a complete job lifecycle with mocked responses"""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock process for different commands
            def create_mock_process(stdout_data, returncode=0):
                mock_process = type(
                    "MockProcess",
                    (),
                    {
                        "returncode": returncode,
                        "communicate": lambda: asyncio.create_future(),
                    },
                )()
                mock_process.communicate().set_result((stdout_data, ""))
                return mock_process

            # Set up different responses for different commands
            responses = [
                ('{"job_uuid": "test-123", "status": "running"}', 0),  # run job
                (
                    '{"uuid": "test-123", "status": "running", "command": "echo"}',
                    0,
                ),  # get status
                ("Hello World\n", 0),  # get logs
                ('{"uuid": "test-123", "status": "completed"}', 0),  # stop job
            ]

            response_iter = iter(responses)
            mock_subprocess.side_effect = lambda *args, **kwargs: create_mock_process(
                *next(response_iter)
            )

            # Test job lifecycle
            # 1. Run job
            result1 = await mock_server._execute_tool(
                "joblet_run_job", {"command": "echo", "args": ["Hello World"]}
            )
            assert "test-123" in result1

            # 2. Get status
            result2 = await mock_server._execute_tool(
                "joblet_get_job_status", {"job_uuid": "test-123"}
            )
            assert "running" in result2

            # 3. Get logs
            result3 = await mock_server._execute_tool(
                "joblet_get_job_logs", {"job_uuid": "test-123"}
            )
            assert "Hello World" in result3

            # 4. Stop job
            result4 = await mock_server._execute_tool(
                "joblet_stop_job", {"job_uuid": "test-123"}
            )
            assert "test-123" in result4

            # Verify all commands were called
            assert mock_subprocess.call_count == 4
