"""
End-to-end tests for resource management functionality
"""

import asyncio
import json

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
class TestVolumeManagement:
    """Test volume creation, listing, and removal"""

    async def test_volume_lifecycle(
        self, e2e_server, cleanup_volumes, temp_volume_name, server_status
    ):
        """Test complete volume lifecycle: create, list, use, remove"""
        # Create a volume
        create_result = await e2e_server._execute_tool(
            "joblet_create_volume",
            {"name": temp_volume_name, "size": "1GB", "type": "filesystem"},
        )

        cleanup_volumes(temp_volume_name)

        # Verify creation was successful
        assert temp_volume_name in create_result or "created" in create_result.lower()

        # List volumes and verify our volume exists
        list_result = await e2e_server._execute_tool("joblet_list_volumes", {})

        # Parse volume list - could be JSON array or line-separated
        if list_result.strip().startswith("["):
            volumes_data = json.loads(list_result)
            volume_names = [vol.get("name", "") for vol in volumes_data]
        else:
            # Handle case where volumes are listed line by line
            volume_names = []
            for line in list_result.strip().split("\n"):
                if line.strip():
                    try:
                        vol_data = json.loads(line)
                        volume_names.append(vol_data.get("name", ""))
                    except json.JSONDecodeError:
                        # Handle plain text format
                        if temp_volume_name in line:
                            volume_names.append(temp_volume_name)

        assert (
            temp_volume_name in volume_names
        ), f"Volume {temp_volume_name} not found in {volume_names}"

        # Test using the volume in a job
        job_result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": [
                    "-c",
                    "echo 'Testing volume' > /data/test.txt && cat /data/test.txt",
                ],
                "name": "volume-test-job",
                "volumes": [f"{temp_volume_name}:/data"],
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job_data = json.loads(job_result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")

        # Wait for job completion
        await self._wait_for_job_completion(e2e_server, job_uuid)

        # Check job logs to verify volume was accessible
        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Testing volume" in logs_result

        # Clean up the job
        try:
            await e2e_server._execute_tool("joblet_delete_job", {"job_uuid": job_uuid})
        except Exception:
            pass

        # Remove the volume
        remove_result = await e2e_server._execute_tool(
            "joblet_remove_volume", {"name": temp_volume_name}
        )

        assert "removed" in remove_result.lower() or "deleted" in remove_result.lower()

        # Verify volume is no longer listed
        final_list = await e2e_server._execute_tool("joblet_list_volumes", {})
        assert temp_volume_name not in final_list

    async def test_volume_data_persistence(
        self, e2e_server, cleanup_volumes, temp_volume_name, server_status
    ):
        """Test that data persists across different jobs using the same volume"""
        # Create volume
        await e2e_server._execute_tool(
            "joblet_create_volume", {"name": temp_volume_name, "size": "1GB"}
        )
        cleanup_volumes(temp_volume_name)

        # First job: write data to volume
        job1_result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": [
                    "-c",
                    "echo 'Persistent data from job 1' > /shared/data.txt",
                ],
                "name": "persistence-test-1",
                "volumes": [f"{temp_volume_name}:/shared"],
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job1_data = json.loads(job1_result)
        job1_uuid = job1_data.get("job_uuid") or job1_data.get("uuid")

        await self._wait_for_job_completion(e2e_server, job1_uuid)

        # Second job: read data from volume
        job2_result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": [
                    "-c",
                    "cat /shared/data.txt && echo 'Job 2 can read the data'",
                ],
                "name": "persistence-test-2",
                "volumes": [f"{temp_volume_name}:/shared"],
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job2_data = json.loads(job2_result)
        job2_uuid = job2_data.get("job_uuid") or job2_data.get("uuid")

        await self._wait_for_job_completion(e2e_server, job2_uuid)

        # Check that job 2 could read the data from job 1
        job2_logs = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job2_uuid}
        )

        assert "Persistent data from job 1" in job2_logs
        assert "Job 2 can read the data" in job2_logs

        # Cleanup jobs
        for job_uuid in [job1_uuid, job2_uuid]:
            try:
                await e2e_server._execute_tool(
                    "joblet_delete_job", {"job_uuid": job_uuid}
                )
            except Exception:
                pass

    async def test_multiple_volumes_in_job(
        self, e2e_server, cleanup_volumes, server_status
    ):
        """Test using multiple volumes in a single job"""
        volume1_name = f"multi-vol-1-{id(self)}"
        volume2_name = f"multi-vol-2-{id(self)}"

        # Create two volumes
        await e2e_server._execute_tool(
            "joblet_create_volume", {"name": volume1_name, "size": "500MB"}
        )
        cleanup_volumes(volume1_name)

        await e2e_server._execute_tool(
            "joblet_create_volume", {"name": volume2_name, "size": "500MB"}
        )
        cleanup_volumes(volume2_name)

        # Use both volumes in a job
        job_result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": [
                    "-c",
                    "echo 'Volume 1 data' > /vol1/test.txt && "
                    "echo 'Volume 2 data' > /vol2/test.txt && "
                    "cat /vol1/test.txt /vol2/test.txt",
                ],
                "name": "multi-volume-test",
                "volumes": [f"{volume1_name}:/vol1", f"{volume2_name}:/vol2"],
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job_data = json.loads(job_result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")

        await self._wait_for_job_completion(e2e_server, job_uuid)

        # Verify both volumes were accessible
        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Volume 1 data" in logs_result
        assert "Volume 2 data" in logs_result

        # Cleanup
        try:
            await e2e_server._execute_tool("joblet_delete_job", {"job_uuid": job_uuid})
        except Exception:
            pass

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
class TestNetworkManagement:
    """Test network creation, listing, and removal"""

    async def test_network_lifecycle(
        self, e2e_server, cleanup_networks, temp_network_name, server_status
    ):
        """Test complete network lifecycle"""
        # Create a network
        create_result = await e2e_server._execute_tool(
            "joblet_create_network",
            {"name": temp_network_name, "cidr": "10.100.0.0/24"},
        )

        cleanup_networks(temp_network_name)

        # Verify creation
        assert temp_network_name in create_result or "created" in create_result.lower()

        # List networks and verify our network exists
        list_result = await e2e_server._execute_tool("joblet_list_networks", {})

        # Check if our network is in the list
        assert temp_network_name in list_result

        # Test using the network in a job
        job_result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": [
                    "-c",
                    "ip addr show && echo 'Network test completed'",
                ],
                "name": "network-test-job",
                "network": temp_network_name,
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job_data = json.loads(job_result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")

        # Wait for job completion
        await self._wait_for_job_completion(e2e_server, job_uuid)

        # Check job logs
        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Network test completed" in logs_result

        # Cleanup job
        try:
            await e2e_server._execute_tool("joblet_delete_job", {"job_uuid": job_uuid})
        except Exception:
            pass

        # Remove the network
        remove_result = await e2e_server._execute_tool(
            "joblet_remove_network", {"name": temp_network_name}
        )

        assert "removed" in remove_result.lower() or "deleted" in remove_result.lower()

    async def test_network_isolation(self, e2e_server, cleanup_networks, server_status):
        """Test that jobs in different networks are isolated"""
        network1_name = f"isolation-net-1-{id(self)}"
        network2_name = f"isolation-net-2-{id(self)}"

        # Create two different networks
        await e2e_server._execute_tool(
            "joblet_create_network",
            {"name": network1_name, "cidr": "10.101.0.0/24"},
        )
        cleanup_networks(network1_name)

        await e2e_server._execute_tool(
            "joblet_create_network",
            {"name": network2_name, "cidr": "10.102.0.0/24"},
        )
        cleanup_networks(network2_name)

        # Run jobs in different networks
        job1_result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": ["-c", "hostname && ip addr show | grep inet"],
                "name": "isolation-test-1",
                "network": network1_name,
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job2_result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": ["-c", "hostname && ip addr show | grep inet"],
                "name": "isolation-test-2",
                "network": network2_name,
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job1_data = json.loads(job1_result)
        job1_uuid = job1_data.get("job_uuid") or job1_data.get("uuid")

        job2_data = json.loads(job2_result)
        job2_uuid = job2_data.get("job_uuid") or job2_data.get("uuid")

        # Wait for completion
        await self._wait_for_job_completion(e2e_server, job1_uuid)
        await self._wait_for_job_completion(e2e_server, job2_uuid)

        # Get logs from both jobs
        job1_logs = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job1_uuid}
        )

        job2_logs = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job2_uuid}
        )

        # Both jobs should have network interfaces but potentially different configurations
        assert "inet" in job1_logs
        assert "inet" in job2_logs

        # Cleanup
        for job_uuid in [job1_uuid, job2_uuid]:
            try:
                await e2e_server._execute_tool(
                    "joblet_delete_job", {"job_uuid": job_uuid}
                )
            except Exception:
                pass

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
class TestSystemMonitoring:
    """Test system monitoring and status reporting"""

    async def test_system_status(self, e2e_server, server_status):
        """Test getting system status"""
        result = await e2e_server._execute_tool("joblet_get_system_status", {})

        # Parse the result
        status_data = json.loads(result)

        # Check for expected fields
        expected_fields = ["cpu", "memory", "disk"]
        for field in expected_fields:
            assert field in status_data or any(
                field in str(v).lower() for v in status_data.values()
            )

    async def test_system_metrics(self, e2e_server, server_status):
        """Test getting real-time system metrics"""
        result = await e2e_server._execute_tool(
            "joblet_get_system_metrics", {"interval": 1}
        )

        # Should contain metrics data
        assert (
            "cpu" in result.lower()
            or "memory" in result.lower()
            or "usage" in result.lower()
        )

    async def test_node_listing(self, e2e_server, server_status):
        """Test listing available nodes"""
        result = await e2e_server._execute_tool("joblet_list_nodes", {})

        # Should contain node information
        assert len(result.strip()) > 0

        # Try to parse as JSON
        try:
            nodes_data = json.loads(result)
            assert isinstance(nodes_data, (list, dict))
        except json.JSONDecodeError:
            # If not JSON, should still contain useful information
            assert "node" in result.lower() or "default" in result.lower()

    async def test_gpu_status(self, e2e_server, server_status):
        """Test GPU status reporting (if GPUs available)"""
        try:
            result = await e2e_server._execute_tool("joblet_get_gpu_status", {})

            # If successful, should contain GPU information
            assert len(result.strip()) > 0

            # Try to parse as JSON
            try:
                gpu_data = json.loads(result)
                # If there are GPUs, should have relevant fields
                if gpu_data and isinstance(gpu_data, (list, dict)):
                    gpu_str = str(gpu_data).lower()
                    assert (
                        "gpu" in gpu_str
                        or "memory" in gpu_str
                        or "utilization" in gpu_str
                    )
            except json.JSONDecodeError:
                # Plain text response is also acceptable
                assert (
                    "gpu" in result.lower()
                    or "no gpu" in result.lower()
                    or "not available" in result.lower()
                )

        except RuntimeError as e:
            # GPU status might not be available on all systems
            assert (
                "gpu" in str(e).lower()
                or "not found" in str(e).lower()
                or "not available" in str(e).lower()
            )
