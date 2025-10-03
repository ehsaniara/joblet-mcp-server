#!/usr/bin/env python3
"""
Joblet MCP Server (SDK-based implementation)

A Model Context Protocol server that exposes Joblet's job orchestration
and resource management capabilities using joblet-sdk-python directly.
"""

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel

# Try to import joblet SDK, fall back gracefully if not available
try:
    from joblet import JobletClient
    from joblet.services import (
        JobService,
        MonitoringService,
        NetworkService,
        RuntimeService,
        VolumeService,
    )

    SDK_AVAILABLE = True
except ImportError:
    JobletClient = None
    JobService = MonitoringService = VolumeService = NetworkService = RuntimeService = (
        None
    )
    SDK_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("joblet-mcp-server")


class JobletConfig(BaseModel):
    """Configuration for Joblet connection"""

    config_file: Optional[str] = None
    node_name: str = "default"


class JobletMCPServerSDK:
    """MCP Server for Joblet job orchestration system using joblet-sdk-python"""

    def __init__(self, config: JobletConfig):
        self.config = config
        self.server = Server("joblet-mcp-server")
        self.client: Optional[JobletClient] = None
        self._setup_handlers()

    async def _get_client(self) -> JobletClient:
        """Get or create the Joblet client"""
        if self.client is None:
            # Use default config discovery if no config file specified
            config_file = self.config.config_file
            if config_file is None:
                # Default to ~/.rnx/rnx-config.yml
                default_config = Path.home() / ".rnx" / "rnx-config.yml"
                if default_config.exists():
                    config_file = str(default_config)

            self.client = JobletClient(
                config_file=config_file, node_name=self.config.node_name
            )
        return self.client

    def _setup_handlers(self):
        """Set up MCP request handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available Joblet tools"""
            return [
                # Job Management Tools
                Tool(
                    name="joblet_run_job",
                    description="Execute a new job with resource specifications",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Command to execute",
                            },
                            "args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Command arguments",
                            },
                            "name": {
                                "type": "string",
                                "description": "Optional job name",
                            },
                            "max_cpu": {
                                "type": "integer",
                                "description": "Maximum CPU percentage",
                            },
                            "cpu_cores": {
                                "type": "string",
                                "description": "CPU cores specification",
                            },
                            "max_memory": {
                                "type": "integer",
                                "description": "Maximum memory in MB",
                            },
                            "max_iobps": {
                                "type": "integer",
                                "description": "Maximum I/O operations per second",
                            },
                            "gpu_count": {
                                "type": "integer",
                                "description": "Number of GPUs to allocate",
                            },
                            "gpu_memory_mb": {
                                "type": "integer",
                                "description": "Minimum GPU memory in MB",
                            },
                            "schedule": {
                                "type": "string",
                                "description": "Schedule time (RFC3339 format)",
                            },
                            "network": {
                                "type": "string",
                                "description": "Network configuration",
                            },
                            "volumes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Volumes to mount (format: volume_name:/mount/path)",
                            },
                            "runtime": {
                                "type": "string",
                                "description": "Runtime specification",
                            },
                            "work_dir": {
                                "type": "string",
                                "description": "Working directory",
                            },
                            "environment": {
                                "type": "object",
                                "description": "Environment variables",
                            },
                            "secret_environment": {
                                "type": "object",
                                "description": "Secret environment variables",
                            },
                            "uploads": {
                                "type": "array",
                                "description": "Files to upload to job workspace",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "path": {
                                            "type": "string",
                                            "description": "File path",
                                        },
                                        "content": {
                                            "type": "string",
                                            "description": (
                                                "File content "
                                                "(base64 encoded for binary)"
                                            ),
                                        },
                                        "mode": {
                                            "type": "integer",
                                            "description": "File permissions",
                                        },
                                        "is_directory": {
                                            "type": "boolean",
                                            "description": "Whether this is a directory",
                                        },
                                    },
                                    "required": ["path", "content"],
                                },
                            },
                        },
                        "required": ["command"],
                    },
                ),
                Tool(
                    name="joblet_list_jobs",
                    description="List all jobs with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "description": "Filter by job status",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of jobs to return",
                            },
                        },
                    },
                ),
                Tool(
                    name="joblet_get_job_status",
                    description="Get detailed status and metadata for a specific job",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_uuid": {
                                "type": "string",
                                "description": "Job UUID (supports short form)",
                            },
                        },
                        "required": ["job_uuid"],
                    },
                ),
                Tool(
                    name="joblet_get_job_logs",
                    description="Stream or retrieve job execution logs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_uuid": {
                                "type": "string",
                                "description": "Job UUID (supports short form)",
                            },
                            "lines": {
                                "type": "integer",
                                "description": "Number of log lines to retrieve",
                            },
                            "follow": {
                                "type": "boolean",
                                "description": "Follow logs (stream mode)",
                            },
                        },
                        "required": ["job_uuid"],
                    },
                ),
                Tool(
                    name="joblet_stop_job",
                    description="Stop a currently running job",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_uuid": {
                                "type": "string",
                                "description": "Job UUID (supports short form)",
                            },
                        },
                        "required": ["job_uuid"],
                    },
                ),
                Tool(
                    name="joblet_cancel_job",
                    description="Cancel a scheduled job before it starts",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_uuid": {
                                "type": "string",
                                "description": "Job UUID (supports short form)",
                            },
                        },
                        "required": ["job_uuid"],
                    },
                ),
                Tool(
                    name="joblet_delete_job",
                    description="Remove a job and its associated data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_uuid": {
                                "type": "string",
                                "description": "Job UUID (supports short form)",
                            },
                        },
                        "required": ["job_uuid"],
                    },
                ),
                Tool(
                    name="joblet_delete_all_jobs",
                    description="Bulk delete all non-running jobs",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                # Workflow Management Tools
                Tool(
                    name="joblet_run_workflow",
                    description="Execute a multi-job workflow from YAML configuration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow": {
                                "type": "string",
                                "description": "Workflow filename",
                            },
                            "yaml_content": {
                                "type": "string",
                                "description": "YAML workflow content",
                            },
                            "workflow_files": {
                                "type": "array",
                                "description": "Workflow files to upload",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "path": {"type": "string"},
                                        "content": {"type": "string"},
                                        "mode": {"type": "integer"},
                                        "is_directory": {"type": "boolean"},
                                    },
                                },
                            },
                        },
                        "required": ["workflow"],
                    },
                ),
                Tool(
                    name="joblet_get_workflow_status",
                    description="Get detailed status of a workflow and its jobs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_uuid": {
                                "type": "string",
                                "description": "Workflow UUID",
                            },
                        },
                        "required": ["workflow_uuid"],
                    },
                ),
                Tool(
                    name="joblet_list_workflows",
                    description="List all workflow executions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_completed": {
                                "type": "boolean",
                                "description": "Include completed workflows",
                            },
                        },
                    },
                ),
                Tool(
                    name="joblet_get_workflow_jobs",
                    description="Get all jobs in a specific workflow",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_uuid": {
                                "type": "string",
                                "description": "Workflow UUID",
                            },
                        },
                        "required": ["workflow_uuid"],
                    },
                ),
                # Resource Management Tools
                Tool(
                    name="joblet_create_volume",
                    description="Create a persistent storage volume",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Volume name",
                            },
                            "size": {
                                "type": "string",
                                "description": "Volume size (e.g., '10GB', '500MB')",
                            },
                            "type": {
                                "type": "string",
                                "description": "Volume type",
                            },
                        },
                        "required": ["name", "size"],
                    },
                ),
                Tool(
                    name="joblet_list_volumes",
                    description="List available storage volumes and their usage",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="joblet_remove_volume",
                    description="Delete a storage volume",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Volume name",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="joblet_create_network",
                    description="Set up an isolated network for jobs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Network name",
                            },
                            "cidr": {
                                "type": "string",
                                "description": "CIDR notation for network (e.g., '10.0.1.0/24')",
                            },
                        },
                        "required": ["name", "cidr"],
                    },
                ),
                Tool(
                    name="joblet_list_networks",
                    description="List available network configurations",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="joblet_remove_network",
                    description="Remove a network configuration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Network name",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                # Monitoring Tools
                Tool(
                    name="joblet_get_system_status",
                    description="Get comprehensive server status and health information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="joblet_get_system_metrics",
                    description="Get real-time system performance metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "interval": {
                                "type": "integer",
                                "description": "Metrics collection interval in seconds",
                            },
                        },
                    },
                ),
                Tool(
                    name="joblet_get_gpu_status",
                    description="Get GPU utilization and temperature monitoring",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="joblet_list_nodes",
                    description="Show available Joblet nodes and their status",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                # Runtime Management Tools
                Tool(
                    name="joblet_list_runtimes",
                    description="List available runtime environments",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="joblet_install_runtime",
                    description="Install a new runtime environment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "runtime_spec": {
                                "type": "string",
                                "description": "Runtime specification",
                            },
                            "repository": {
                                "type": "string",
                                "description": "GitHub repository (e.g., owner/repo)",
                            },
                            "branch": {
                                "type": "string",
                                "description": "Repository branch",
                            },
                            "path": {
                                "type": "string",
                                "description": "Path in repository",
                            },
                            "force_reinstall": {
                                "type": "boolean",
                                "description": "Force reinstallation",
                            },
                            "stream": {
                                "type": "boolean",
                                "description": "Stream installation progress",
                            },
                        },
                        "required": ["runtime_spec"],
                    },
                ),
                Tool(
                    name="joblet_remove_runtime",
                    description="Remove a runtime environment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "runtime": {
                                "type": "string",
                                "description": "Runtime name to remove",
                            },
                        },
                        "required": ["runtime"],
                    },
                ),
                Tool(
                    name="joblet_get_runtime_info",
                    description="Get detailed information about a runtime environment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "runtime": {
                                "type": "string",
                                "description": "Runtime name",
                            },
                        },
                        "required": ["runtime"],
                    },
                ),
                Tool(
                    name="joblet_test_runtime",
                    description="Test a runtime environment to verify it works correctly",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "runtime": {
                                "type": "string",
                                "description": "Runtime name to test",
                            },
                        },
                        "required": ["runtime"],
                    },
                ),
                Tool(
                    name="joblet_validate_runtime",
                    description="Validate a runtime specification without installing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "runtime_spec": {
                                "type": "string",
                                "description": "Runtime specification to validate",
                            },
                        },
                        "required": ["runtime_spec"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute a Joblet tool"""
            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(type="text", text=result)]
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                raise RuntimeError(f"Tool execution failed: {str(e)}")

    async def _get_session(self):
        """Get the current request session for sending notifications"""
        try:
            request_context = self.server.request_context()
            return request_context.session
        except (LookupError, AttributeError):
            return None

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a Joblet tool using the SDK"""
        client = await self._get_client()

        try:
            if tool_name == "joblet_run_job":

                # Handle file uploads if provided
                uploads = []
                if arguments.get("uploads"):
                    for upload in arguments["uploads"]:
                        uploads.append(
                            {
                                "path": upload.get("path", ""),
                                "content": (
                                    upload.get("content", "").encode()
                                    if isinstance(upload.get("content"), str)
                                    else upload.get("content", b"")
                                ),
                                "mode": upload.get("mode", 0o644),
                                "is_directory": upload.get("is_directory", False),
                            }
                        )

                result = client.jobs.run_job(
                    command=arguments["command"],
                    args=arguments.get("args", []),
                    name=arguments.get("name"),
                    max_cpu=arguments.get("max_cpu"),
                    cpu_cores=arguments.get("cpu_cores"),
                    max_memory=arguments.get("max_memory"),
                    max_iobps=arguments.get("max_iobps"),  # Fixed parameter name
                    gpu_count=arguments.get("gpu_count"),
                    gpu_memory_mb=arguments.get("gpu_memory_mb"),
                    schedule=arguments.get("schedule"),
                    network=arguments.get("network"),
                    volumes=arguments.get("volumes", []),
                    runtime=arguments.get("runtime"),
                    work_dir=arguments.get("work_dir"),
                    environment=arguments.get("environment", {}),
                    secret_environment=arguments.get("secret_environment", {}),
                    uploads=uploads if uploads else None,
                )
                return str(result)

            elif tool_name == "joblet_list_jobs":
                jobs = client.jobs.list_jobs(
                    status=arguments.get("status"),
                    limit=arguments.get("limit"),
                )
                return str(jobs)

            elif tool_name == "joblet_get_job_status":
                status = client.jobs.get_job_status(arguments["job_uuid"])
                return str(status)

            elif tool_name == "joblet_get_job_logs":
                # get_job_logs returns an iterator of log chunks
                logs_iterator = client.jobs.get_job_logs(arguments["job_uuid"])
                log_chunks = []

                # Check if streaming/follow mode is requested
                follow = arguments.get("follow", False)

                try:
                    if follow:
                        # Stream logs using MCP notifications
                        session = await self._get_session()
                        chunk_count = 0

                        # Get progress token from request context if available
                        progress_token = None
                        try:
                            request_context = self.server.request_context()
                            if request_context.meta:
                                progress_token = request_context.meta.progressToken
                        except (LookupError, AttributeError):
                            pass

                        for chunk in logs_iterator:
                            chunk_text = chunk.decode("utf-8", errors="replace")
                            log_chunks.append(chunk_text)
                            chunk_count += 1

                            # Send notifications if session is available
                            if session:
                                try:
                                    # Send log chunk as logging notification
                                    await session.send_log_message(
                                        level="info",
                                        logger="joblet_logs",
                                        data=chunk_text,
                                    )

                                    # Send progress update if token provided
                                    if progress_token:
                                        await session.send_progress_notification(
                                            progress_token=progress_token,
                                            progress=chunk_count,
                                            total=None,  # Unknown total for streaming logs
                                            message=f"Received {chunk_count} log chunks",
                                        )
                                except Exception as notif_err:
                                    logger.warning(
                                        f"Failed to send notification: {notif_err}"
                                    )

                        return (
                            "\n".join(log_chunks) if log_chunks else "No logs available"
                        )
                    else:
                        # Non-streaming mode: collect limited chunks
                        max_chunks = arguments.get("lines", 100)
                        chunk_count = 0
                        for chunk in logs_iterator:
                            if chunk_count >= max_chunks:
                                break
                            log_chunks.append(chunk.decode("utf-8", errors="replace"))
                            chunk_count += 1

                        return (
                            "\n".join(log_chunks) if log_chunks else "No logs available"
                        )
                except Exception as e:
                    return f"Error retrieving logs: {str(e)}"

            elif tool_name == "joblet_stop_job":
                # job_service = JobService(client)
                result = client.jobs.stop_job(arguments["job_uuid"])
                return str(result)

            elif tool_name == "joblet_cancel_job":
                # job_service = JobService(client)
                result = client.jobs.cancel_job(arguments["job_uuid"])
                return str(result)

            elif tool_name == "joblet_delete_job":
                # job_service = JobService(client)
                result = client.jobs.delete_job(arguments["job_uuid"])
                return str(result)

            elif tool_name == "joblet_delete_all_jobs":
                # job_service = JobService(client)
                result = client.jobs.delete_all_jobs()
                return str(result)

            elif tool_name == "joblet_create_volume":
                result = client.volumes.create_volume(
                    name=arguments["name"],
                    size=arguments["size"],
                    volume_type=arguments.get("type"),
                )
                return str(result)

            elif tool_name == "joblet_list_volumes":
                volumes = client.volumes.list_volumes()
                return str(volumes)

            elif tool_name == "joblet_remove_volume":
                result = client.volumes.remove_volume(arguments["name"])
                return str(result)

            elif tool_name == "joblet_create_network":
                result = client.networks.create_network(
                    name=arguments["name"], cidr=arguments["cidr"]
                )
                return str(result)

            elif tool_name == "joblet_list_networks":
                networks = client.networks.list_networks()
                return str(networks)

            elif tool_name == "joblet_remove_network":
                result = client.networks.remove_network(arguments["name"])
                return str(result)

            elif tool_name == "joblet_get_system_status":
                # monitoring_service = MonitoringService(client)
                status = client.monitoring.get_system_status()
                return str(status)

            elif tool_name == "joblet_get_system_metrics":
                # Use stream_system_metrics to get one sample
                metrics_stream = client.monitoring.stream_system_metrics(
                    interval_seconds=1,
                    metric_types=arguments.get("metric_types", []),
                )
                # Get the first metrics sample
                for metrics in metrics_stream:
                    return str(metrics)
                return str({"error": "No metrics available"})

            elif tool_name == "joblet_get_gpu_status":
                # GPU status is part of system status
                status = client.monitoring.get_system_status()
                # Extract GPU information from system status
                gpu_info = (
                    status.get("gpu", {})
                    if "gpu" in status
                    else {"error": "No GPU information available"}
                )
                return str(gpu_info)

            elif tool_name == "joblet_list_nodes":
                # Get configuration info to list available nodes
                # This might need to be implemented differently depending on actual SDK capabilities
                try:
                    status = client.monitoring.get_system_status()
                    host_info = status.get("host", {})
                    nodes = [
                        {
                            "node_id": host_info.get("node_id", "unknown"),
                            "status": "active",
                        }
                    ]
                    return str(nodes)
                except Exception as e:
                    return str({"error": f"Could not list nodes: {str(e)}"})

            elif tool_name == "joblet_list_runtimes":
                # runtime_service = RuntimeService(client)
                runtimes = client.runtimes.list_runtimes()
                return str(runtimes)

            elif tool_name == "joblet_install_runtime":
                # Determine if installing from GitHub or local based on repository parameter
                if arguments.get("repository"):
                    result = client.runtimes.install_runtime_from_github(
                        runtime_spec=arguments["runtime_spec"],
                        repository=arguments["repository"],
                        branch=arguments.get("branch"),
                        path=arguments.get("path"),
                        force_reinstall=arguments.get("force_reinstall", False),
                        stream=arguments.get("stream", False),
                    )
                else:
                    # For local installation, we'd need file data
                    result = {
                        "error": (
                            "Local runtime installation requires file data - "
                            "use joblet_install_runtime_from_local"
                        )
                    }
                return str(result)

            elif tool_name == "joblet_remove_runtime":
                # runtime_service = RuntimeService(client)
                result = client.runtimes.remove_runtime(arguments["runtime"])
                return str(result)

            # Workflow tools
            elif tool_name == "joblet_run_workflow":
                # job_service = JobService(client)
                workflow_files = []
                if arguments.get("workflow_files"):
                    for file_info in arguments["workflow_files"]:
                        workflow_files.append(
                            {
                                "path": file_info.get("path", ""),
                                "content": file_info.get("content", "").encode(),
                                "mode": file_info.get("mode", 0o644),
                                "is_directory": file_info.get("is_directory", False),
                            }
                        )
                result = client.jobs.run_workflow(
                    workflow=arguments["workflow"],
                    yaml_content=arguments.get("yaml_content"),
                    workflow_files=workflow_files if workflow_files else None,
                )
                return str(result)

            elif tool_name == "joblet_get_workflow_status":
                # job_service = JobService(client)
                result = client.jobs.get_workflow_status(arguments["workflow_uuid"])
                return str(result)

            elif tool_name == "joblet_list_workflows":
                # job_service = JobService(client)
                result = client.jobs.list_workflows(
                    include_completed=arguments.get("include_completed", False)
                )
                return str(result)

            elif tool_name == "joblet_get_workflow_jobs":
                # job_service = JobService(client)
                result = client.jobs.get_workflow_jobs(arguments["workflow_uuid"])
                return str(result)

            # Additional runtime tools
            elif tool_name == "joblet_get_runtime_info":
                # runtime_service = RuntimeService(client)
                result = client.runtimes.get_runtime_info(arguments["runtime"])
                return str(result)

            elif tool_name == "joblet_test_runtime":
                # runtime_service = RuntimeService(client)
                result = client.runtimes.test_runtime(arguments["runtime"])
                return str(result)

            elif tool_name == "joblet_validate_runtime":
                # runtime_service = RuntimeService(client)
                # Note: This method may not exist in current SDK, will implement validation logic
                try:
                    result = client.runtimes.validate_runtime(arguments["runtime_spec"])
                except AttributeError:
                    # Fallback: try to get runtime info to validate it exists
                    try:
                        client.runtimes.get_runtime_info(arguments["runtime_spec"])
                        result = {
                            "valid": True,
                            "message": "Runtime specification appears valid",
                        }
                    except Exception as e:
                        result = {
                            "valid": False,
                            "message": f"Runtime validation failed: {str(e)}",
                        }
                return str(result)

            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"SDK tool execution failed for {tool_name}: {e}")
            raise RuntimeError(f"Failed to execute {tool_name}: {str(e)}")

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="joblet-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Joblet MCP Server (SDK-based)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration:
The server looks for configuration in ~/.rnx/rnx-config.yml by default.
You can specify a different config file with --config.

Example usage:
  joblet-mcp-server
  joblet-mcp-server --config /path/to/config.yml
  joblet-mcp-server --node viewer
        """,
    )

    parser.add_argument(
        "--config",
        help="Path to Joblet configuration file (default: ~/.rnx/rnx-config.yml)",
    )
    parser.add_argument(
        "--node",
        default="default",
        help="Node name from configuration (default: default)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check if SDK is available
    if not SDK_AVAILABLE:
        logger.error("joblet-sdk is not installed. Please install it with:")
        logger.error("  pip install 'joblet-mcp-server[sdk]'")
        logger.error("Or use the CLI-based server instead:")
        logger.error("  joblet-mcp-server-cli")
        raise ImportError("joblet-sdk package is required for SDK-based server")

    # Create configuration
    config = JobletConfig(
        config_file=args.config,
        node_name=args.node,
    )

    # Create and run the server
    server = JobletMCPServerSDK(config)

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
