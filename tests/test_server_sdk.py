"""
Tests for the Joblet MCP Server SDK
"""

from unittest.mock import MagicMock

import pytest

from joblet_mcp_server.server_sdk import JobletConfig, JobletMCPServerSDK


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    return JobletConfig(
        config_file="/test/config.yaml",
        node_name="test-node",
    )


@pytest.fixture
def mcp_server_sdk(mock_config):
    """Create a JobletMCPServerSDK instance"""
    return JobletMCPServerSDK(mock_config)


class TestJobletMCPServerSDK:
    """Test cases for JobletMCPServerSDK"""

    def test_server_initialization(self, mcp_server_sdk, mock_config):
        """Test server initializes correctly"""
        assert mcp_server_sdk.config == mock_config
        assert mcp_server_sdk.server is not None
        assert mcp_server_sdk.client is None

    def test_config_defaults(self):
        """Test configuration defaults"""
        config = JobletConfig()
        assert config.config_file is None
        assert config.node_name == "default"

    def test_config_custom_values(self):
        """Test configuration with custom values"""
        config = JobletConfig(
            config_file="/custom/config.yaml",
            node_name="custom-node",
        )
        assert config.config_file == "/custom/config.yaml"
        assert config.node_name == "custom-node"


class TestToolExecution:
    """Test tool execution with mocked JobletClient"""

    @pytest.mark.asyncio
    async def test_run_job_tool(self, mcp_server_sdk):
        """Test joblet_run_job tool execution"""
        mock_client = MagicMock()
        mock_client.jobs.run_job.return_value = {"job_uuid": "test-uuid-123"}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool(
            "joblet_run_job",
            {"command": "echo", "args": ["hello"]},
        )

        assert "test-uuid-123" in result
        mock_client.jobs.run_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_jobs_tool(self, mcp_server_sdk):
        """Test joblet_list_jobs tool execution"""
        mock_client = MagicMock()
        mock_client.jobs.list_jobs.return_value = [
            {"job_uuid": "job1", "status": "running"},
            {"job_uuid": "job2", "status": "completed"},
        ]
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool("joblet_list_jobs", {})

        assert "job1" in result
        assert "job2" in result
        mock_client.jobs.list_jobs.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_job_status_tool(self, mcp_server_sdk):
        """Test joblet_get_job_status tool execution"""
        mock_client = MagicMock()
        mock_client.jobs.get_job_status.return_value = {
            "job_uuid": "test-uuid",
            "status": "running",
        }
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool(
            "joblet_get_job_status",
            {"job_uuid": "test-uuid"},
        )

        assert "test-uuid" in result
        assert "running" in result
        mock_client.jobs.get_job_status.assert_called_once_with("test-uuid")

    @pytest.mark.asyncio
    async def test_stop_job_tool(self, mcp_server_sdk):
        """Test joblet_stop_job tool execution"""
        mock_client = MagicMock()
        mock_client.jobs.stop_job.return_value = {"success": True}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool(
            "joblet_stop_job",
            {"job_uuid": "test-uuid"},
        )

        assert "success" in result
        mock_client.jobs.stop_job.assert_called_once_with("test-uuid")

    @pytest.mark.asyncio
    async def test_cancel_job_tool(self, mcp_server_sdk):
        """Test joblet_cancel_job tool execution"""
        mock_client = MagicMock()
        mock_client.jobs.cancel_job.return_value = {"success": True}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool(
            "joblet_cancel_job",
            {"job_uuid": "test-uuid"},
        )

        assert "success" in result
        mock_client.jobs.cancel_job.assert_called_once_with("test-uuid")

    @pytest.mark.asyncio
    async def test_delete_job_tool(self, mcp_server_sdk):
        """Test joblet_delete_job tool execution"""
        mock_client = MagicMock()
        mock_client.jobs.delete_job.return_value = {"success": True}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool(
            "joblet_delete_job",
            {"job_uuid": "test-uuid"},
        )

        assert "success" in result
        mock_client.jobs.delete_job.assert_called_once_with("test-uuid")

    @pytest.mark.asyncio
    async def test_delete_all_jobs_tool(self, mcp_server_sdk):
        """Test joblet_delete_all_jobs tool execution"""
        mock_client = MagicMock()
        mock_client.jobs.delete_all_jobs.return_value = {"deleted": 5}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool("joblet_delete_all_jobs", {})

        assert "deleted" in result
        mock_client.jobs.delete_all_jobs.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_volume_tool(self, mcp_server_sdk):
        """Test joblet_create_volume tool execution"""
        mock_client = MagicMock()
        mock_client.volumes.create_volume.return_value = {"name": "test-vol"}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool(
            "joblet_create_volume",
            {"name": "test-vol", "size": "10GB"},
        )

        assert "test-vol" in result
        mock_client.volumes.create_volume.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_volumes_tool(self, mcp_server_sdk):
        """Test joblet_list_volumes tool execution"""
        mock_client = MagicMock()
        mock_client.volumes.list_volumes.return_value = [
            {"name": "vol1"},
            {"name": "vol2"},
        ]
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool("joblet_list_volumes", {})

        assert "vol1" in result
        assert "vol2" in result
        mock_client.volumes.list_volumes.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_volume_tool(self, mcp_server_sdk):
        """Test joblet_remove_volume tool execution"""
        mock_client = MagicMock()
        mock_client.volumes.remove_volume.return_value = {"success": True}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool(
            "joblet_remove_volume",
            {"name": "test-vol"},
        )

        assert "success" in result
        mock_client.volumes.remove_volume.assert_called_once_with("test-vol")

    @pytest.mark.asyncio
    async def test_create_network_tool(self, mcp_server_sdk):
        """Test joblet_create_network tool execution"""
        mock_client = MagicMock()
        mock_client.networks.create_network.return_value = {"name": "test-net"}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool(
            "joblet_create_network",
            {"name": "test-net", "cidr": "10.0.1.0/24"},
        )

        assert "test-net" in result
        mock_client.networks.create_network.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_networks_tool(self, mcp_server_sdk):
        """Test joblet_list_networks tool execution"""
        mock_client = MagicMock()
        mock_client.networks.list_networks.return_value = [{"name": "net1"}]
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool("joblet_list_networks", {})

        assert "net1" in result
        mock_client.networks.list_networks.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_network_tool(self, mcp_server_sdk):
        """Test joblet_remove_network tool execution"""
        mock_client = MagicMock()
        mock_client.networks.remove_network.return_value = {"success": True}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool(
            "joblet_remove_network",
            {"name": "test-net"},
        )

        assert "success" in result
        mock_client.networks.remove_network.assert_called_once_with("test-net")

    @pytest.mark.asyncio
    async def test_get_system_status_tool(self, mcp_server_sdk):
        """Test joblet_get_system_status tool execution"""
        mock_client = MagicMock()
        mock_client.monitoring.get_system_status.return_value = {"status": "healthy"}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool("joblet_get_system_status", {})

        assert "healthy" in result
        mock_client.monitoring.get_system_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_runtimes_tool(self, mcp_server_sdk):
        """Test joblet_list_runtimes tool execution"""
        mock_client = MagicMock()
        mock_client.runtimes.list_runtimes.return_value = [{"name": "python:3.11"}]
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool("joblet_list_runtimes", {})

        assert "python:3.11" in result
        mock_client.runtimes.list_runtimes.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_runtime_tool(self, mcp_server_sdk):
        """Test joblet_remove_runtime tool execution"""
        mock_client = MagicMock()
        mock_client.runtimes.remove_runtime.return_value = {"success": True}
        mcp_server_sdk.client = mock_client

        result = await mcp_server_sdk._execute_tool(
            "joblet_remove_runtime",
            {"runtime": "python:3.11"},
        )

        assert "success" in result
        mock_client.runtimes.remove_runtime.assert_called_once_with("python:3.11")

    @pytest.mark.asyncio
    async def test_unknown_tool(self, mcp_server_sdk):
        """Test handling unknown tool names"""
        mock_client = MagicMock()
        mcp_server_sdk.client = mock_client

        with pytest.raises(RuntimeError, match="Unknown tool"):
            await mcp_server_sdk._execute_tool("unknown_tool", {})

    @pytest.mark.asyncio
    async def test_tool_execution_error(self, mcp_server_sdk):
        """Test error handling in tool execution"""
        mock_client = MagicMock()
        mock_client.jobs.get_job_status.side_effect = Exception("Job not found")
        mcp_server_sdk.client = mock_client

        with pytest.raises(RuntimeError, match="Failed to execute"):
            await mcp_server_sdk._execute_tool(
                "joblet_get_job_status",
                {"job_uuid": "nonexistent"},
            )
