"""
Joblet MCP Server

A Model Context Protocol server that provides comprehensive access to Joblet's
job orchestration and resource management capabilities.
"""

__version__ = "1.0.0"
__author__ = "Jay Ehsaniara"
__description__ = "MCP server for Joblet job orchestration system"

from .server import JobletMCPServer

__all__ = ["JobletMCPServer"]
