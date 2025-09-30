#!/usr/bin/env python3
"""
Joblet MCP Server

A Model Context Protocol server that exposes Joblet's job orchestration
and resource management capabilities as MCP tools.
"""

import argparse
import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool
from pydantic import BaseModel

# Try to import SDK-based server first
try:
    from .server_sdk import JobletConfig as JobletConfigSDK
    from .server_sdk import JobletMCPServerSDK

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("joblet-mcp-server")


class JobletConfig(BaseModel):
    """Configuration for Joblet connection"""

    rnx_binary_path: str = "rnx"
    config_file: Optional[str] = None
    node_name: str = "default"
    json_output: bool = True


class JobletMCPServer:
    """MCP Server for Joblet job orchestration system"""

    def __init__(self, config: JobletConfig):
        self.config = config
        self.server = Server("joblet-mcp-server")
        self._setup_handlers()

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
                                "description": "Volumes to mount",
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
                        },
                        "required": ["command"],
                    },
                ),
                Tool(
                    name="joblet_list_jobs",
                    description="List all jobs or workflows with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow": {
                                "type": "boolean",
                                "description": "List workflows instead of jobs",
                            },
                            "include_completed": {
                                "type": "boolean",
                                "description": "Include completed workflows",
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
                    description="Stream or retrieve execution logs from a job",
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
                    description="Cancel a scheduled job (status becomes CANCELED)",
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
                    description="Remove a job and its data permanently",
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
                    inputSchema={"type": "object", "properties": {}},
                ),
                # Workflow Tools
                Tool(
                    name="joblet_run_workflow",
                    description="Execute a multi-job workflow with dependencies",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_file": {
                                "type": "string",
                                "description": "Path to workflow YAML file",
                            },
                            "workflow_content": {
                                "type": "string",
                                "description": "YAML workflow content",
                            },
                        },
                        "required": ["workflow_file"],
                    },
                ),
                Tool(
                    name="joblet_get_workflow_status",
                    description="Monitor workflow progress and job coordination",
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
                # Volume Management Tools
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
                                "description": "Volume size (e.g., '10GB')",
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
                    description="List available volumes and their usage",
                    inputSchema={"type": "object", "properties": {}},
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
                # Network Management Tools
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
                                "description": "CIDR block (e.g., '10.0.1.0/24')",
                            },
                        },
                        "required": ["name", "cidr"],
                    },
                ),
                Tool(
                    name="joblet_list_networks",
                    description="List network configurations and usage",
                    inputSchema={"type": "object", "properties": {}},
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
                    description="Get comprehensive server status and availability",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="joblet_get_system_metrics",
                    description="Real-time system performance metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "interval": {
                                "type": "integer",
                                "description": "Update interval in seconds",
                            },
                        },
                    },
                ),
                Tool(
                    name="joblet_get_gpu_status",
                    description="GPU utilization and temperature monitoring",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="joblet_list_nodes",
                    description="Show available Joblet nodes from configuration",
                    inputSchema={"type": "object", "properties": {}},
                ),
                # Runtime Management Tools
                Tool(
                    name="joblet_list_runtimes",
                    description="List available runtime environments",
                    inputSchema={"type": "object", "properties": {}},
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
                                "description": "Git repository URL",
                            },
                            "branch": {
                                "type": "string",
                                "description": "Git branch",
                            },
                            "force_reinstall": {
                                "type": "boolean",
                                "description": "Force reinstallation",
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
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls by executing rnx commands"""
            try:
                result = await self._execute_tool(name, arguments)
                return CallToolResult(content=[TextContent(type="text", text=result)])
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                )

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a Joblet tool by calling the rnx CLI"""

        # Build base command
        cmd = [self.config.rnx_binary_path]

        # Add global flags
        if self.config.config_file:
            cmd.extend(["--config", self.config.config_file])
        if self.config.node_name != "default":
            cmd.extend(["--node", self.config.node_name])
        if self.config.json_output:
            cmd.append("--json")

        # Map tool names to rnx commands
        if tool_name == "joblet_run_job":
            cmd.extend(["job", "run"])
            cmd.append(arguments["command"])

            if "args" in arguments:
                cmd.extend(arguments["args"])

            # Add optional flags
            if "name" in arguments:
                cmd.extend(["--name", arguments["name"]])
            if "max_cpu" in arguments:
                cmd.extend(["--max-cpu", str(arguments["max_cpu"])])
            if "cpu_cores" in arguments:
                cmd.extend(["--cpu-cores", arguments["cpu_cores"]])
            if "max_memory" in arguments:
                cmd.extend(["--max-memory", str(arguments["max_memory"])])
            if "max_iobps" in arguments:
                cmd.extend(["--max-iobps", str(arguments["max_iobps"])])
            if "gpu_count" in arguments:
                cmd.extend(["--gpu", str(arguments["gpu_count"])])
            if "gpu_memory_mb" in arguments:
                cmd.extend(["--gpu-memory", str(arguments["gpu_memory_mb"])])
            if "schedule" in arguments:
                cmd.extend(["--schedule", arguments["schedule"]])
            if "network" in arguments:
                cmd.extend(["--network", arguments["network"]])
            if "volumes" in arguments:
                for volume in arguments["volumes"]:
                    cmd.extend(["--volume", volume])
            if "runtime" in arguments:
                cmd.extend(["--runtime", arguments["runtime"]])
            if "work_dir" in arguments:
                cmd.extend(["--work-dir", arguments["work_dir"]])
            if "environment" in arguments:
                for key, value in arguments["environment"].items():
                    cmd.extend(["--env", f"{key}={value}"])
            if "secret_environment" in arguments:
                for key, value in arguments["secret_environment"].items():
                    cmd.extend(["--secret-env", f"{key}={value}"])

        elif tool_name == "joblet_list_jobs":
            cmd.extend(["job", "list"])
            if arguments.get("workflow"):
                cmd.append("--workflow")
            if arguments.get("include_completed"):
                cmd.append("--include-completed")

        elif tool_name == "joblet_get_job_status":
            cmd.extend(["job", "status", arguments["job_uuid"]])

        elif tool_name == "joblet_get_job_logs":
            cmd.extend(["job", "log", arguments["job_uuid"]])
            if "lines" in arguments:
                cmd.extend(["--lines", str(arguments["lines"])])

        elif tool_name == "joblet_stop_job":
            cmd.extend(["job", "stop", arguments["job_uuid"]])

        elif tool_name == "joblet_cancel_job":
            cmd.extend(["job", "cancel", arguments["job_uuid"]])

        elif tool_name == "joblet_delete_job":
            cmd.extend(["job", "delete", arguments["job_uuid"]])

        elif tool_name == "joblet_delete_all_jobs":
            cmd.extend(["job", "delete-all"])

        elif tool_name == "joblet_run_workflow":
            cmd.extend(["job", "run", "--workflow", arguments["workflow_file"]])

        elif tool_name == "joblet_get_workflow_status":
            cmd.extend(["job", "status", arguments["workflow_uuid"]])

        elif tool_name == "joblet_list_workflows":
            cmd.extend(["job", "list", "--workflow"])
            if arguments.get("include_completed"):
                cmd.append("--include-completed")

        elif tool_name == "joblet_create_volume":
            cmd.extend(["volume", "create", arguments["name"], arguments["size"]])
            if "type" in arguments:
                cmd.extend(["--type", arguments["type"]])

        elif tool_name == "joblet_list_volumes":
            cmd.extend(["volume", "list"])

        elif tool_name == "joblet_remove_volume":
            cmd.extend(["volume", "remove", arguments["name"]])

        elif tool_name == "joblet_create_network":
            cmd.extend(["network", "create", arguments["name"], arguments["cidr"]])

        elif tool_name == "joblet_list_networks":
            cmd.extend(["network", "list"])

        elif tool_name == "joblet_remove_network":
            cmd.extend(["network", "remove", arguments["name"]])

        elif tool_name == "joblet_get_system_status":
            cmd.extend(["monitor", "status"])

        elif tool_name == "joblet_get_system_metrics":
            if arguments.get("interval"):
                cmd.extend(
                    [
                        "monitor",
                        "watch",
                        "--interval",
                        str(arguments["interval"]),
                    ]
                )
            else:
                cmd.extend(["monitor", "top"])

        elif tool_name == "joblet_get_gpu_status":
            cmd.extend(["monitor", "gpu"])

        elif tool_name == "joblet_list_nodes":
            cmd.extend(["nodes"])

        elif tool_name == "joblet_list_runtimes":
            cmd.extend(["runtime", "list"])

        elif tool_name == "joblet_install_runtime":
            cmd.extend(["runtime", "install", arguments["runtime_spec"]])
            if "repository" in arguments:
                cmd.extend(["--repository", arguments["repository"]])
            if "branch" in arguments:
                cmd.extend(["--branch", arguments["branch"]])
            if arguments.get("force_reinstall"):
                cmd.append("--force")

        elif tool_name == "joblet_remove_runtime":
            cmd.extend(["runtime", "remove", arguments["runtime"]])

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Execute the command
        logger.info(f"Executing command: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            # Decode bytes to string
            stdout_str = stdout.decode() if stdout else ""
            stderr_str = stderr.decode() if stderr else ""

            if process.returncode == 0:
                return (
                    stdout_str.strip()
                    if stdout_str
                    else "Command executed successfully"
                )
            else:
                error_msg = (
                    stderr_str.strip()
                    if stderr_str
                    else f"Command failed with exit code {process.returncode}"
                )
                raise RuntimeError(error_msg)

        except FileNotFoundError:
            raise RuntimeError(
                f"rnx binary not found at: {self.config.rnx_binary_path}"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to execute command: {str(e)}")

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
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Joblet MCP Server - Model Context Protocol server for Joblet"
    )
    parser.add_argument(
        "--rnx-binary", default="rnx", help="Path to rnx binary (default: rnx)"
    )
    parser.add_argument("--config", help="Path to Joblet configuration file")
    parser.add_argument(
        "--node",
        default="default",
        help="Node name from configuration (default: default)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Prefer SDK-based server if available
    if SDK_AVAILABLE:
        logger.info("Using SDK-based server (recommended)")
        sdk_config = JobletConfigSDK(
            config_file=args.config,
            node_name=args.node,
        )
        server = JobletMCPServerSDK(sdk_config)
        await server.run()
    else:
        logger.warning("SDK not available, falling back to CLI-based server")
        logger.warning("For better performance, install: pip install joblet-sdk-python")

        # Create configuration for CLI-based server
        config = JobletConfig(
            rnx_binary_path=args.rnx_binary,
            config_file=args.config,
            node_name=args.node,
        )

        # Create and run CLI-based server
        server = JobletMCPServer(config)
        await server.run()


def main_sync():
    """Synchronous main function for script entry point"""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
