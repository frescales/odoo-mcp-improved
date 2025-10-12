#!/usr/bin/env python
"""
MCP Server for Odoo using FastMCP 2.0
Compatible with Claude Web via SSE transport
Simplified version without external dependencies
"""

import os
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import FastMCP
from fastmcp import FastMCP

# Create FastMCP server
mcp = FastMCP("Odoo MCP Server")

# Simple test tool that doesn't require Odoo imports
@mcp.tool()
def hello(name: str) -> str:
    """Say hello to someone
    
    Args:
        name: Name of the person to greet
    
    Returns:
        A greeting message
    """
    return f"Hello, {name}! This is the Odoo MCP Server."

@mcp.tool()
def server_status() -> str:
    """Get server status information
    
    Returns:
        Server status as JSON string
    """
    status = {
        "server": "Odoo MCP Server",
        "status": "running",
        "port": os.getenv("PORT", "8000"),
        "odoo_url": os.getenv("ODOO_URL", "not configured"),
        "odoo_db": os.getenv("ODOO_DB", "not configured")
    }
    return json.dumps(status, indent=2)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info("=" * 60)
    logger.info("Starting Odoo MCP Server (Simplified Test Version)")
    logger.info("=" * 60)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info("")
    logger.info("Available tools:")
    logger.info("  - hello: Test greeting tool")
    logger.info("  - server_status: Get server information")
    logger.info("")
    logger.info("Connect from Claude Web:")
    logger.info(f"  URL: https://n8n-odoo.e2gone.easypanel.host/sse")
    logger.info("=" * 60)
    
    # Run with SSE transport
    # Use explicit parameters to avoid env variable issues
    mcp.run(transport="sse", host=host, port=port)
