"""
Configuration and fixtures for e2e tests
"""

import asyncio
import shutil
import tempfile
from pathlib import Path

import pytest

try:
    from joblet_mcp_server.server_sdk import JobletConfig as JobletConfigSDK
    from joblet_mcp_server.server_sdk import (
        JobletMCPServerSDK,
    )

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

from joblet_mcp_server.server import JobletConfig, JobletMCPServer


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def skip_if_no_rnx():
    """Skip tests if rnx binary is not available"""
    rnx_path = shutil.which("rnx")
    if not rnx_path:
        pytest.skip("rnx binary not found - skipping e2e tests")
    return rnx_path


@pytest.fixture
async def rnx_version(skip_if_no_rnx):
    """Get rnx version and validate it's working"""
    try:
        process = await asyncio.create_subprocess_exec(
            "rnx",
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            text=True,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            pytest.skip(f"rnx not working: {stderr}")

        return stdout.strip()
    except Exception as e:
        pytest.skip(f"Failed to check rnx version: {e}")


@pytest.fixture
def e2e_config(skip_if_no_rnx):
    """Create configuration for e2e tests"""
    if SDK_AVAILABLE:
        # Use SDK-based server (recommended)
        return JobletConfigSDK(
            config_file=None,  # Use default config discovery (~/.rnx/rnx-config.yml)
            node_name="default",
        )
    else:
        # Fall back to CLI-based server
        return JobletConfig(
            rnx_binary_path=skip_if_no_rnx,
            config_file=None,  # Use default config discovery
            node_name="default",
            json_output=True,
        )


@pytest.fixture
def e2e_server(e2e_config):
    """Create MCP server for e2e tests"""
    if SDK_AVAILABLE:
        return JobletMCPServerSDK(e2e_config)
    else:
        return JobletMCPServer(e2e_config)


@pytest.fixture
async def server_status(e2e_server):
    """Check if Joblet server is available and get status"""
    try:
        result = await e2e_server._execute_tool("joblet_get_system_status", {})
        return result
    except Exception as e:
        pytest.skip(f"Joblet server not available: {e}")


@pytest.fixture
async def available_runtimes(e2e_server):
    """Get list of available runtimes"""
    try:
        result = await e2e_server._execute_tool("joblet_list_runtimes", {})
        return result
    except Exception as e:
        pytest.skip(f"Failed to list runtimes: {e}")


@pytest.fixture
def temp_volume_name():
    """Generate a unique temporary volume name"""
    import uuid

    return f"e2e-test-vol-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def temp_network_name():
    """Generate a unique temporary network name"""
    import uuid

    return f"e2e-test-net-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def temp_job_name():
    """Generate a unique temporary job name"""
    import uuid

    return f"e2e-test-job-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_workspace():
    """Create a temporary workspace for file-based tests"""
    with tempfile.TemporaryDirectory(prefix="joblet-e2e-") as tmpdir:
        workspace = Path(tmpdir)

        # Create some test files
        test_script = workspace / "test_script.py"
        test_script.write_text(
            """
import sys
import os
print(f"Hello from Python {sys.version_info.major}.{sys.version_info.minor}")
print(f"Working directory: {os.getcwd()}")
print(f"Args: {sys.argv[1:] if len(sys.argv) > 1 else 'none'}")

# Test environment variables
if os.getenv("TEST_ENV"):
    print(f"Test environment: {os.getenv('TEST_ENV')}")

# Simple computation
result = sum(range(100))
print(f"Computation result: {result}")
"""
        )

        test_data = workspace / "test_data.txt"
        test_data.write_text("Hello, Joblet!\nThis is test data.\n")

        yield workspace


@pytest.fixture
async def cleanup_jobs(e2e_server):
    """Cleanup fixture that runs after tests to clean up any leftover jobs"""
    created_jobs = []

    def track_job(job_id: str):
        created_jobs.append(job_id)

    yield track_job

    # Cleanup
    for job_id in created_jobs:
        try:
            await e2e_server._execute_tool("joblet_delete_job", {"job_uuid": job_id})
        except Exception:
            pass  # Ignore cleanup errors


@pytest.fixture
async def cleanup_volumes(e2e_server):
    """Cleanup fixture for volumes"""
    created_volumes = []

    def track_volume(volume_name: str):
        created_volumes.append(volume_name)

    yield track_volume

    # Cleanup
    for volume_name in created_volumes:
        try:
            await e2e_server._execute_tool(
                "joblet_remove_volume", {"name": volume_name}
            )
        except Exception:
            pass  # Ignore cleanup errors


@pytest.fixture
async def cleanup_networks(e2e_server):
    """Cleanup fixture for networks"""
    created_networks = []

    def track_network(network_name: str):
        created_networks.append(network_name)

    yield track_network

    # Cleanup
    for network_name in created_networks:
        try:
            await e2e_server._execute_tool(
                "joblet_remove_network", {"name": network_name}
            )
        except Exception:
            pass  # Ignore cleanup errors


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "e2e: marks tests as end-to-end tests requiring real environment",
    )
    config.addinivalue_line("markers", "slow: marks tests as slow-running tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add appropriate markers"""
    for item in items:
        # Add e2e marker to all tests in e2e directory
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Mark tests that run actual jobs as slow
        if any(
            keyword in item.name.lower() for keyword in ["job", "workflow", "runtime"]
        ):
            item.add_marker(pytest.mark.slow)
