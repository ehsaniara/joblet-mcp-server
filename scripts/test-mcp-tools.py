#!/usr/bin/env python3
"""
Simple test script for Joblet MCP Server tools

This script helps test individual MCP tools without setting up a full MCP client.
Useful for development and debugging.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the server
sys.path.insert(0, str(Path(__file__).parent.parent))

from joblet_mcp_server.server import JobletMCPServer, JobletConfig


async def test_tool(tool_name: str, arguments: dict, config: JobletConfig):
    """Test a single MCP tool"""
    server = JobletMCPServer(config)

    try:
        result = await server._execute_tool(tool_name, arguments)
        print(f"✓ Tool '{tool_name}' executed successfully")
        print("Result:")

        # Try to parse as JSON for pretty printing
        try:
            parsed = json.loads(result)
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError:
            print(result)

        return True

    except Exception as e:
        print(f"✗ Tool '{tool_name}' failed: {e}")
        return False


async def test_list_tools(config: JobletConfig):
    """Test listing all available tools"""
    server = JobletMCPServer(config)

    # Get the list tools handler
    handler = None
    for h in server.server._list_tools_handlers:
        handler = h
        break

    if handler is None:
        print("✗ No list tools handler found")
        return False

    try:
        tools = await handler()
        print(f"✓ Found {len(tools)} tools:")

        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        return True

    except Exception as e:
        print(f"✗ Failed to list tools: {e}")
        return False


async def run_interactive_test(config: JobletConfig):
    """Run interactive tool testing"""
    server = JobletMCPServer(config)

    print("Joblet MCP Server - Interactive Tool Testing")
    print("=" * 50)

    while True:
        print("\nAvailable commands:")
        print("  list - List all available tools")
        print("  test <tool_name> [args_json] - Test a specific tool")
        print("  examples - Show some example commands")
        print("  quit - Exit")

        try:
            command = input("\n> ").strip()

            if command == "quit":
                break

            elif command == "list":
                await test_list_tools(config)

            elif command == "examples":
                print_examples()

            elif command.startswith("test "):
                parts = command.split(" ", 2)
                tool_name = parts[1]

                if len(parts) > 2:
                    try:
                        arguments = json.loads(parts[2])
                    except json.JSONDecodeError as e:
                        print(f"✗ Invalid JSON arguments: {e}")
                        continue
                else:
                    arguments = {}

                await test_tool(tool_name, arguments, config)

            else:
                print("Unknown command. Type 'quit' to exit.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            print("\nExiting...")
            break


def print_examples():
    """Print example commands"""
    examples = [
        ("joblet_list_nodes", "{}"),
        ("joblet_list_jobs", "{}"),
        ("joblet_get_system_status", "{}"),
        ("joblet_list_volumes", "{}"),
        ("joblet_list_networks", "{}"),
        ("joblet_list_runtimes", "{}"),
        ('joblet_run_job', '{"command": "echo", "args": ["hello", "world"]}'),
        ('joblet_run_job', '{"command": "python", "args": ["-c", "print(\\"Hello from Python\\")"], "runtime": "python-3.11"}'),
        ('joblet_run_job', '{"command": "python", "args": ["-c", "import numpy; print(f\\"NumPy: {numpy.__version__}\\")"], "runtime": "python-3.11-ml"}'),
        ('joblet_run_job', '{"command": "java", "args": ["-version"], "runtime": "openjdk-21"}'),
        ('joblet_get_job_status', '{"job_uuid": "your-job-id"}'),
        ('joblet_create_volume', '{"name": "test-vol", "size": "1GB"}'),
    ]

    print("\nExample commands:")
    for tool_name, args in examples:
        print(f"  test {tool_name} {args}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test Joblet MCP Server tools"
    )
    parser.add_argument(
        "--rnx-binary",
        default="rnx",
        help="Path to rnx binary (default: rnx)"
    )
    parser.add_argument(
        "--config",
        help="Path to Joblet configuration file"
    )
    parser.add_argument(
        "--node",
        default="default",
        help="Node name from configuration (default: default)"
    )
    parser.add_argument(
        "--tool",
        help="Specific tool to test"
    )
    parser.add_argument(
        "--args",
        help="JSON arguments for the tool",
        default="{}"
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List all available tools and exit"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )

    args = parser.parse_args()

    # Create configuration
    config = JobletConfig(
        rnx_binary_path=args.rnx_binary,
        config_file=args.config,
        node_name=args.node,
    )

    async def run():
        if args.list_tools:
            return await test_list_tools(config)
        elif args.interactive:
            await run_interactive_test(config)
            return True
        elif args.tool:
            try:
                arguments = json.loads(args.args)
            except json.JSONDecodeError as e:
                print(f"✗ Invalid JSON arguments: {e}")
                return False
            return await test_tool(args.tool, arguments, config)
        else:
            print("No action specified. Use --help for options.")
            return False

    try:
        success = asyncio.run(run())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()