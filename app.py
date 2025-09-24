#!/usr/bin/env python
"""
HTTP/SSE MCP Server for Odoo Integration
Compatible with n8n MCP client tool and EasyPanel deployment
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from src.odoo_mcp.server import mcp as odoo_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan handler"""
    logger.info("Starting Odoo MCP HTTP Server...")
    yield
    logger.info("Stopping Odoo MCP HTTP Server...")

# Create FastAPI app
app = FastAPI(
    title="Odoo MCP Server",
    description="HTTP/SSE MCP Server for Odoo Integration",
    version="1.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy", 
            "service": "odoo-mcp-server",
            "version": "1.1.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "service": "Odoo MCP Server",
        "version": "1.1.0",
        "transport": "HTTP/SSE",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp",
            "sse": "/sse",
            "docs": "/docs"
        },
        "environment": {
            "odoo_url": os.getenv("ODOO_URL", "not_configured"),
            "odoo_db": os.getenv("ODOO_DB", "not_configured"),
            "odoo_username": os.getenv("ODOO_USERNAME", "not_configured")
        }
    }

async def process_mcp_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process MCP request using the FastMCP server"""
    try:
        method = request_data.get("method", "")
        params = request_data.get("params", {})
        request_id = request_data.get("id")
        
        logger.info(f"Processing MCP request: {method}")
        
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "serverInfo": {
                        "name": "odoo-mcp-server",
                        "version": "1.1.0"
                    }
                }
            }
            
        elif method == "tools/list":
            # Get tools directly from FastMCP
            tools = []
            
            # Access tools from the FastMCP instance
            if hasattr(odoo_mcp_server, '_app') and hasattr(odoo_mcp_server._app, 'tool_registry'):
                tool_registry = odoo_mcp_server._app.tool_registry
                for tool_name, tool_info in tool_registry.items():
                    tools.append({
                        "name": tool_name,
                        "description": tool_info.get("description", ""),
                        "inputSchema": tool_info.get("input_schema", {})
                    })
            else:
                # Fallback: manually list known tools
                known_tools = [
                    {"name": "execute_method", "description": "Execute a custom method on an Odoo model"},
                    {"name": "search_employee", "description": "Search for employees by name"},
                    {"name": "search_holidays", "description": "Search for holidays within a date range"},
                    {"name": "search_sales_orders", "description": "Search sales orders with advanced filters"},
                    {"name": "create_sales_order", "description": "Create a new sales order"},
                    {"name": "analyze_sales_performance", "description": "Analyze sales performance in a period"},
                    {"name": "search_purchase_orders", "description": "Search purchase orders with advanced filters"},
                    {"name": "create_purchase_order", "description": "Create a new purchase order"},
                    {"name": "analyze_supplier_performance", "description": "Analyze supplier performance"},
                    {"name": "check_product_availability", "description": "Check stock availability for products"},
                    {"name": "create_inventory_adjustment", "description": "Create inventory adjustment"},
                    {"name": "analyze_inventory_turnover", "description": "Analyze inventory turnover"},
                    {"name": "search_journal_entries", "description": "Search journal entries"},
                    {"name": "create_journal_entry", "description": "Create journal entry"},
                    {"name": "analyze_financial_ratios", "description": "Calculate financial ratios"}
                ]
                tools = known_tools
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools}
            }
            
        elif method == "resources/list":
            resources = [
                {
                    "uri": "odoo://models",
                    "name": "Odoo Models",
                    "description": "List all available models in the Odoo system",
                    "mimeType": "application/json"
                },
                {
                    "uri": "odoo://model/{model_name}",
                    "name": "Model Info",
                    "description": "Get detailed information about a specific model",
                    "mimeType": "application/json"
                }
            ]
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"resources": resources}
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            try:
                # Create a mock context for the tool call
                class MockContext:
                    class MockRequestContext:
                        class MockLifespanContext:
                            def __init__(self):
                                from src.odoo_mcp.odoo_client import get_odoo_client
                                self.odoo = get_odoo_client()
                        
                        def __init__(self):
                            self.lifespan_context = self.MockLifespanContext()
                    
                    def __init__(self):
                        self.request_context = self.MockRequestContext()
                
                ctx = MockContext()
                
                # Import and call the appropriate function
                if tool_name == "search_employee":
                    from src.odoo_mcp.server import search_employee
                    result = search_employee(ctx, **arguments)
                elif tool_name == "search_holidays":
                    from src.odoo_mcp.server import search_holidays
                    result = search_holidays(ctx, **arguments)
                elif tool_name == "execute_method":
                    from src.odoo_mcp.server import execute_method
                    result = execute_method(ctx, **arguments)
                elif tool_name == "search_sales_orders":
                    from src.odoo_mcp.tools_sales import search_sales_orders
                    result = search_sales_orders(ctx, **arguments)
                elif tool_name == "create_sales_order":
                    from src.odoo_mcp.tools_sales import create_sales_order
                    result = create_sales_order(ctx, **arguments)
                elif tool_name == "analyze_sales_performance":
                    from src.odoo_mcp.tools_sales import analyze_sales_performance
                    result = analyze_sales_performance(ctx, **arguments)
                elif tool_name == "search_purchase_orders":
                    from src.odoo_mcp.tools_purchase import search_purchase_orders
                    result = search_purchase_orders(ctx, **arguments)
                elif tool_name == "create_purchase_order":
                    from src.odoo_mcp.tools_purchase import create_purchase_order
                    result = create_purchase_order(ctx, **arguments)
                elif tool_name == "analyze_supplier_performance":
                    from src.odoo_mcp.tools_purchase import analyze_supplier_performance
                    result = analyze_supplier_performance(ctx, **arguments)
                elif tool_name == "check_product_availability":
                    from src.odoo_mcp.tools_inventory import check_product_availability
                    result = check_product_availability(ctx, **arguments)
                elif tool_name == "create_inventory_adjustment":
                    from src.odoo_mcp.tools_inventory import create_inventory_adjustment
                    result = create_inventory_adjustment(ctx, **arguments)
                elif tool_name == "analyze_inventory_turnover":
                    from src.odoo_mcp.tools_inventory import analyze_inventory_turnover
                    result = analyze_inventory_turnover(ctx, **arguments)
                elif tool_name == "search_journal_entries":
                    from src.odoo_mcp.tools_accounting import search_journal_entries
                    result = search_journal_entries(ctx, **arguments)
                elif tool_name == "create_journal_entry":
                    from src.odoo_mcp.tools_accounting import create_journal_entry
                    result = create_journal_entry(ctx, **arguments)
                elif tool_name == "analyze_financial_ratios":
                    from src.odoo_mcp.tools_accounting import analyze_financial_ratios
                    result = analyze_financial_ratios(ctx, **arguments)
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2, default=str)
                            }
                        ]
                    }
                }
                
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution failed: {str(e)}"
                    }
                }
                
        elif method == "resources/read":
            uri = params.get("uri")
            
            try:
                if uri == "odoo://models":
                    from src.odoo_mcp.odoo_client import get_odoo_client
                    odoo_client = get_odoo_client()
                    models = odoo_client.get_models()
                    result = json.dumps(models, indent=2)
                else:
                    result = json.dumps({"error": f"Resource not found: {uri}"}, indent=2)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": result
                            }
                        ]
                    }
                }
            except Exception as e:
                logger.error(f"Resource read error: {e}")
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Resource read failed: {str(e)}"
                    }
                }
                
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing MCP request: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            "id": request_data.get("id")
        }

@app.post("/sse")
async def handle_sse_mcp(request: Request):
    """Handle MCP requests via Server-Sent Events"""
    logger.info("New SSE MCP connection")
    
    async def event_generator():
        try:
            body = await request.body()
            if body:
                try:
                    request_data = json.loads(body.decode())
                    response = await process_mcp_request(request_data)
                    yield f"data: {json.dumps(response)}\n\n"
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                        "id": None
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
            
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            
        except Exception as e:
            logger.error(f"SSE connection error: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Connection error: {str(e)}"},
                "id": None
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    """Handle MCP requests via standard HTTP POST"""
    try:
        body = await request.body()
        request_data = json.loads(body.decode())
        response = await process_mcp_request(request_data)
        return JSONResponse(content=response)
        
    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                "id": None
            }
        )
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request_data.get("id") if 'request_data' in locals() else None
            }
        )

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Environment check:")
    logger.info(f"  ODOO_URL: {os.getenv('ODOO_URL', 'NOT SET')}")
    logger.info(f"  ODOO_DB: {os.getenv('ODOO_DB', 'NOT SET')}")
    logger.info(f"  ODOO_USERNAME: {os.getenv('ODOO_USERNAME', 'NOT SET')}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
