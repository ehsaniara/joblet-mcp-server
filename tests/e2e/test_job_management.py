"""
End-to-end tests for job management functionality
"""

import asyncio
import json
from typing import Any, Dict

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
class TestBasicJobManagement:
    """Test basic job management operations"""

    async def test_simple_echo_job(
        self, e2e_server, cleanup_jobs, temp_job_name, server_status
    ):
        """Test running a simple echo job"""
        # Run a basic echo job
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "echo",
                "args": ["Hello, E2E Test!"],
                "name": temp_job_name,
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        # Parse the result to get job UUID
        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        assert job_uuid, f"No job UUID in result: {result}"

        cleanup_jobs(job_uuid)

        # Wait a moment for the job to start
        await asyncio.sleep(2)

        # Check job status
        status_result = await e2e_server._execute_tool(
            "joblet_get_job_status", {"job_uuid": job_uuid}
        )

        status_data = json.loads(status_result)
        assert status_data.get("command") == "echo"
        assert "Hello, E2E Test!" in str(status_data.get("args", []))

        # Wait for job completion
        max_wait = 30
        wait_time = 0
        final_status = None

        while wait_time < max_wait:
            status_result = await e2e_server._execute_tool(
                "joblet_get_job_status", {"job_uuid": job_uuid}
            )
            status_data = json.loads(status_result)
            final_status = status_data.get("status")

            if final_status in ["completed", "failed", "stopped"]:
                break

            await asyncio.sleep(1)
            wait_time += 1

        # Check final status
        assert (
            final_status == "completed"
        ), f"Job did not complete successfully: {final_status}"

        # Get and verify logs
        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Hello, E2E Test!" in logs_result

    async def test_job_with_resource_limits(
        self, e2e_server, cleanup_jobs, temp_job_name, server_status
    ):
        """Test job with specific resource limits"""
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": [
                    "-c",
                    "echo 'CPU limit test' && sleep 2 && echo 'Memory test'",
                ],
                "name": temp_job_name,
                "max_cpu": 50,
                "max_memory": 1024,
                "max_io_read": 100,
                "max_io_write": 100,
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        # Wait for completion
        await self._wait_for_job_completion(e2e_server, job_uuid)

        # Verify the job completed and used the specified limits
        status_result = await e2e_server._execute_tool(
            "joblet_get_job_status", {"job_uuid": job_uuid}
        )

        status_data = json.loads(status_result)
        assert status_data.get("status") == "completed"
        assert status_data.get("max_cpu") == 50
        assert status_data.get("max_memory") == 1024

    async def test_job_with_environment_variables(
        self, e2e_server, cleanup_jobs, temp_job_name, server_status
    ):
        """Test job with custom environment variables"""
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": [
                    "-c",
                    'echo "TEST_VAR is: $TEST_VAR" && echo "SECOND_VAR is: $SECOND_VAR"',
                ],
                "name": temp_job_name,
                "max_cpu": 25,
                "max_memory": 512,
                "environment": {"TEST_VAR": "hello_world", "SECOND_VAR": "e2e_testing"},
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_job_completion(e2e_server, job_uuid)

        # Check logs for environment variables
        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "TEST_VAR is: hello_world" in logs_result
        assert "SECOND_VAR is: e2e_testing" in logs_result

    async def test_job_list_and_filter(self, e2e_server, cleanup_jobs, server_status):
        """Test listing jobs and filtering"""
        # Run multiple jobs
        job_uuids = []

        for i in range(3):
            result = await e2e_server._execute_tool(
                "joblet_run_job",
                {
                    "command": "echo",
                    "args": [f"Test job {i}"],
                    "name": f"list-test-job-{i}",
                    "max_cpu": 25,
                    "max_memory": 512,
                },
            )

            job_data = json.loads(result)
            job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
            job_uuids.append(job_uuid)
            cleanup_jobs(job_uuid)

        # Wait a moment for jobs to appear in the list
        await asyncio.sleep(2)

        # List all jobs
        list_result = await e2e_server._execute_tool("joblet_list_jobs", {})

        # Parse the job list
        if list_result.strip().startswith("["):
            jobs_data = json.loads(list_result)
        else:
            # Handle case where it's one job per line
            jobs_data = [
                json.loads(line)
                for line in list_result.strip().split("\n")
                if line.strip()
            ]

        # Verify our jobs are in the list
        job_names = [job.get("name", "") for job in jobs_data]

        for i in range(3):
            assert any(
                f"list-test-job-{i}" in name for name in job_names
            ), f"Job list-test-job-{i} not found in {job_names}"

    async def test_job_cancellation(
        self, e2e_server, cleanup_jobs, temp_job_name, server_status
    ):
        """Test canceling a running job"""
        # Start a long-running job
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": [
                    "-c",
                    "echo 'Starting long job' && sleep 30 && echo 'Should not reach here'",
                ],
                "name": temp_job_name,
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        # Wait for job to start
        await asyncio.sleep(3)

        # Stop the job
        stop_result = await e2e_server._execute_tool(
            "joblet_stop_job", {"job_uuid": job_uuid}
        )

        # Wait a moment for the stop to take effect
        await asyncio.sleep(2)

        # Check that job was stopped
        status_result = await e2e_server._execute_tool(
            "joblet_get_job_status", {"job_uuid": job_uuid}
        )

        status_data = json.loads(status_result)
        assert status_data.get("status") in ["stopped", "cancelled", "failed"]

        # Verify logs show the job was started but not completed
        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Starting long job" in logs_result
        assert "Should not reach here" not in logs_result

    async def test_short_uuid_functionality(
        self, e2e_server, cleanup_jobs, temp_job_name, server_status
    ):
        """Test using short UUIDs (first 8 characters)"""
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "echo",
                "args": ["Short UUID test"],
                "name": temp_job_name,
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job_data = json.loads(result)
        full_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        short_uuid = full_uuid[:8]
        cleanup_jobs(full_uuid)

        await self._wait_for_job_completion(e2e_server, full_uuid)

        # Test that short UUID works for status check
        status_result = await e2e_server._execute_tool(
            "joblet_get_job_status", {"job_uuid": short_uuid}
        )

        status_data = json.loads(status_result)
        assert status_data.get("status") == "completed"

        # Test that short UUID works for logs
        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": short_uuid}
        )

        assert "Short UUID test" in logs_result

    async def _wait_for_job_completion(self, server, job_uuid, max_wait=30):
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
class TestJobDeletion:
    """Test job deletion and cleanup operations"""

    async def test_delete_individual_job(
        self, e2e_server, temp_job_name, server_status
    ):
        """Test deleting a single job"""
        # Create and complete a job
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "echo",
                "args": ["Job to delete"],
                "name": temp_job_name,
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")

        # Wait for completion
        await asyncio.sleep(5)

        # Delete the job
        delete_result = await e2e_server._execute_tool(
            "joblet_delete_job", {"job_uuid": job_uuid}
        )

        # Verify deletion was successful
        assert "deleted" in delete_result.lower() or "success" in delete_result.lower()

        # Verify job no longer exists (should raise an error)
        with pytest.raises(RuntimeError):
            await e2e_server._execute_tool(
                "joblet_get_job_status", {"job_uuid": job_uuid}
            )

    async def test_bulk_delete_completed_jobs(self, e2e_server, server_status):
        """Test bulk deletion of non-running jobs"""
        # Create multiple completed jobs
        job_uuids = []

        for i in range(3):
            result = await e2e_server._execute_tool(
                "joblet_run_job",
                {
                    "command": "echo",
                    "args": [f"Bulk delete test {i}"],
                    "name": f"bulk-delete-{i}",
                    "max_cpu": 25,
                    "max_memory": 512,
                },
            )

            job_data = json.loads(result)
            job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
            job_uuids.append(job_uuid)

        # Wait for all jobs to complete
        await asyncio.sleep(10)

        # Get initial job count
        initial_list = await e2e_server._execute_tool("joblet_list_jobs", {})
        initial_count = len(
            [line for line in initial_list.strip().split("\n") if line.strip()]
        )

        # Bulk delete
        delete_result = await e2e_server._execute_tool("joblet_delete_all_jobs", {})

        # Verify some jobs were deleted
        assert (
            "deleted" in delete_result.lower() or str(len(job_uuids)) in delete_result
        )
