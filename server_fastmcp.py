#!/usr/bin/env python
"""
MCP Server for Odoo using official MCP SDK
Compatible with Claude Web, Claude Desktop, and n8n
"""

import os
import logging
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("Odoo MCP Server")

# Import Odoo client and tools
from src.odoo_mcp.odoo_client import get_odoo_client

# Helper function to get context with Odoo client
def get_odoo_context():
    class MockContext:
        class MockRequestContext:
            class MockLifespanContext:
                def __init__(self):
                    self.odoo = get_odoo_client()
            
            def __init__(self):
                self.lifespan_context = self.MockLifespanContext()
        
        def __init__(self):
            self.request_context = self.MockRequestContext()
    
    return MockContext()

@mcp.tool()
def search_employee(name: str, limit: int = 20) -> str:
    """Search for employees by name in Odoo.
    
    Args:
        name: Name to search for
        limit: Maximum number of results (default: 20)
    
    Returns:
        JSON string with employee data
    """
    try:
        from src.odoo_mcp.server import search_employee as _search_employee
        import json
        ctx = get_odoo_context()
        result = _search_employee(ctx, name=name, limit=limit)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error searching employees: {e}")
        return json.dumps({"error": str(e)})

@mcp.tool()
def search_holidays(start_date: str, end_date: str, employee_id: int = None) -> str:
    """Search for holidays within a date range in Odoo.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        employee_id: Optional employee ID to filter by
    
    Returns:
        JSON string with holiday data
    """
    try:
        from src.odoo_mcp.server import search_holidays as _search_holidays
        import json
        ctx = get_odoo_context()
        result = _search_holidays(ctx, start_date=start_date, end_date=end_date, employee_id=employee_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error searching holidays: {e}")
        return json.dumps({"error": str(e)})

@mcp.tool()
def execute_method(model: str, method: str, args: list = None, kwargs: dict = None) -> str:
    """Execute a custom method on an Odoo model.
    
    Args:
        model: The model name (e.g., 'res.partner')
        method: Method name to execute
        args: Positional arguments (optional)
        kwargs: Keyword arguments (optional)
    
    Returns:
        JSON string with method execution result
    """
    try:
        from src.odoo_mcp.server import execute_method as _execute_method
        import json
        ctx = get_odoo_context()
        result = _execute_method(
            ctx, 
            model=model, 
            method=method, 
            args=args or [], 
            kwargs=kwargs or {}
        )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error executing method: {e}")
        return json.dumps({"error": str(e)})

@mcp.tool()
def search_sales_orders(filters: dict) -> str:
    """Search sales orders with advanced filters in Odoo.
    
    Args:
        filters: Dictionary with filter parameters:
            - date_from: Start date (optional)
            - date_to: End date (optional)
            - partner_id: Customer ID (optional)
            - state: Order state (optional)
            - limit: Max results (default: 20)
    
    Returns:
        JSON string with sales order data
    """
    try:
        from src.odoo_mcp.tools_sales import search_sales_orders as _search_sales_orders
        import json
        ctx = get_odoo_context()
        result = _search_sales_orders(ctx, filters=filters)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error searching sales orders: {e}")
        return json.dumps({"error": str(e)})

@mcp.tool()
def create_sales_order(order: dict) -> str:
    """Create a new sales order in Odoo.
    
    Args:
        order: Dictionary with order data:
            - partner_id: Customer ID (required)
            - order_lines: List of order line dicts (required)
    
    Returns:
        JSON string with created order data
    """
    try:
        from src.odoo_mcp.tools_sales import create_sales_order as _create_sales_order
        import json
        ctx = get_odoo_context()
        result = _create_sales_order(ctx, order=order)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error creating sales order: {e}")
        return json.dumps({"error": str(e)})

@mcp.tool()
def analyze_sales_performance(params: dict) -> str:
    """Analyze sales performance in a period.
    
    Args:
        params: Dictionary with analysis parameters:
            - date_from: Start date (required)
            - date_to: End date (required)
            - group_by: Grouping field (optional)
    
    Returns:
        JSON string with sales analysis
    """
    try:
        from src.odoo_mcp.tools_sales import analyze_sales_performance as _analyze_sales_performance
        import json
        ctx = get_odoo_context()
        result = _analyze_sales_performance(ctx, params=params)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error analyzing sales performance: {e}")
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting Odoo MCP Server with FastMCP")
    logger.info("Environment check:")
    logger.info(f"  ODOO_URL: {os.getenv('ODOO_URL', 'NOT SET')}")
    logger.info(f"  ODOO_DB: {os.getenv('ODOO_DB', 'NOT SET')}")
    logger.info(f"  ODOO_USERNAME: {os.getenv('ODOO_USERNAME', 'NOT SET')}")
    logger.info("")
    logger.info("For Claude Web/Desktop, use:")
    logger.info("  URL: https://your-server.com/sse")
    logger.info("")
    logger.info("For n8n, configure MCP Client with:")
    logger.info("  Transport: HTTP Streamable")
    logger.info("  URL: https://your-server.com/sse")
    
    # Run with SSE transport for remote connections
    mcp.run(transport="sse")
