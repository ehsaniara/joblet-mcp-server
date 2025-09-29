"""
Example E2E tests demonstrating the testing framework

These are simple tests that can be used as templates for creating new E2E tests.
"""

import asyncio
import json

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
class TestExamples:
    """Example E2E tests showing common patterns"""

    async def test_server_connectivity(self, e2e_server, server_status):
        """Test that we can connect to the Joblet server"""
        # This test validates that the MCP server can communicate with Joblet
        # The server_status fixture already checks connectivity
        assert server_status is not None
        print(f"✅ Server status: {len(server_status)} characters")

    async def test_simple_command_execution(
        self, e2e_server, cleanup_jobs, temp_job_name, server_status
    ):
        """Example of running a simple command and checking results"""
        # Run a simple echo command
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "echo",
                "args": ["Hello from E2E test!"],
                "name": temp_job_name,
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        # Parse the job result
        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        assert job_uuid, f"No job UUID in result: {result}"

        # Register for cleanup
        cleanup_jobs(job_uuid)

        # Wait for job completion
        final_status = await self._wait_for_completion(e2e_server, job_uuid)
        assert final_status == "completed"

        # Check the job logs
        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Hello from E2E test!" in logs_result

    async def test_runtime_availability(
        self, e2e_server, available_runtimes, server_status
    ):
        """Example of checking runtime availability"""
        # The available_runtimes fixture provides the list of available runtimes
        print(f"Available runtimes: {available_runtimes}")

        # Check for expected runtimes
        expected = [
            "python-3.11",
            "python-3.11-ml",
            "openjdk-21",
            "graalvmjdk-21",
        ]

        for runtime in expected:
            if runtime in available_runtimes:
                print(f"✅ Runtime {runtime} is available")
            else:
                print(f"⚠️  Runtime {runtime} is not available")

        # At least one runtime should be available
        assert len(available_runtimes.strip()) > 0

    async def test_volume_basic_usage(
        self, e2e_server, cleanup_volumes, temp_volume_name, server_status
    ):
        """Example of basic volume operations"""
        # Create a volume
        create_result = await e2e_server._execute_tool(
            "joblet_create_volume", {"name": temp_volume_name, "size": "100MB"}
        )

        cleanup_volumes(temp_volume_name)

        # Verify creation
        assert temp_volume_name in create_result or "created" in create_result.lower()

        # List volumes to confirm it exists
        list_result = await e2e_server._execute_tool("joblet_list_volumes", {})
        assert temp_volume_name in list_result

        print(f"✅ Volume {temp_volume_name} created and listed successfully")

    async def test_error_handling_example(self, e2e_server, server_status):
        """Example of testing error conditions"""
        # Test with invalid job UUID
        with pytest.raises(RuntimeError):
            await e2e_server._execute_tool(
                "joblet_get_job_status", {"job_uuid": "invalid-uuid-12345"}
            )

        print("✅ Error handling works correctly")

    async def _wait_for_completion(self, server, job_uuid, max_wait=30):
        """Helper method to wait for job completion"""
        wait_time = 0

        while wait_time < max_wait:
            status_result = await server._execute_tool(
                "joblet_get_job_status", {"job_uuid": job_uuid}
            )
            status_data = json.loads(status_result)
            final_status = status_data.get("status")

            if final_status in ["completed", "failed", "stopped"]:
                return final_status

            await asyncio.sleep(1)
            wait_time += 1

        raise TimeoutError(f"Job {job_uuid} did not complete within {max_wait} seconds")


@pytest.mark.e2e
@pytest.mark.asyncio
class TestTemplates:
    """Template tests for common E2E patterns"""

    async def test_job_template(self, e2e_server, cleanup_jobs, server_status):
        """Template for testing job execution"""
        # 1. Submit job
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "echo",  # Replace with your command
                "args": ["test"],  # Replace with your arguments
                "name": "template-job",
                "max_cpu": 25,
                "max_memory": 512,
                # Add other parameters as needed:
                # "runtime": "python-3.11",
                # "environment": {"VAR": "value"},
                # "volumes": ["vol:/mount"],
                # "gpu_count": 1,
            },
        )

        # 2. Extract job UUID and register for cleanup
        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        # 3. Wait for completion
        final_status = await self._wait_for_completion(e2e_server, job_uuid)

        # 4. Verify results
        assert final_status == "completed"

        # 5. Check logs if needed
        logs = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )
        assert "expected_output" in logs

    async def test_resource_template(self, e2e_server, cleanup_volumes, server_status):
        """Template for testing resource management"""
        resource_name = f"test-resource-{id(self)}"

        # 1. Create resource
        create_result = await e2e_server._execute_tool(
            "joblet_create_volume", {"name": resource_name, "size": "1GB"}
        )
        cleanup_volumes(resource_name)

        # 2. Verify creation
        assert resource_name in create_result

        # 3. Use resource (optional)
        # ... use in job ...

        # 4. Cleanup is automatic via fixture

    async def test_runtime_template(
        self, e2e_server, cleanup_jobs, available_runtimes, server_status
    ):
        """Template for testing runtime-specific functionality"""
        runtime_name = "python-3.11"  # Replace with target runtime

        # 1. Check if runtime is available
        if runtime_name not in available_runtimes:
            pytest.skip(f"{runtime_name} runtime not available")

        # 2. Run job with specific runtime
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "python",  # Runtime-specific command
                "args": [
                    "-c",
                    "print('Hello from Python')",
                ],  # Runtime-specific args
                "name": f"{runtime_name}-test",
                "runtime": runtime_name,
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        # 3. Verify runtime-specific behavior
        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_completion(e2e_server, job_uuid)

        logs = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )
        assert "Hello from Python" in logs

    async def _wait_for_completion(self, server, job_uuid, max_wait=30):
        """Helper method to wait for job completion"""
        wait_time = 0

        while wait_time < max_wait:
            status_result = await server._execute_tool(
                "joblet_get_job_status", {"job_uuid": job_uuid}
            )
            status_data = json.loads(status_result)
            final_status = status_data.get("status")

            if final_status in ["completed", "failed", "stopped"]:
                return final_status

            await asyncio.sleep(1)
            wait_time += 1

        raise TimeoutError(f"Job {job_uuid} did not complete within {max_wait} seconds")
