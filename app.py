#!/usr/bin/env python
"""
HTTP/SSE MCP Server for Odoo Integration
Fully compatible with n8n MCP Client node
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List

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

# Tool registry for MCP compatibility
AVAILABLE_TOOLS = {
    "execute_method": {
        "name": "execute_method",
        "description": "Execute a custom method on an Odoo model",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "The model name (e.g., 'res.partner')"},
                "method": {"type": "string", "description": "Method name to execute"},
                "args": {"type": "array", "description": "Positional arguments"},
                "kwargs": {"type": "object", "description": "Keyword arguments"}
            },
            "required": ["model", "method"]
        }
    },
    "search_employee": {
        "name": "search_employee",
        "description": "Search for employees by name",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name to search for"},
                "limit": {"type": "integer", "description": "Maximum results", "default": 20}
            },
            "required": ["name"]
        }
    },
    "search_holidays": {
        "name": "search_holidays", 
        "description": "Search for holidays within a date range",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "employee_id": {"type": "integer", "description": "Optional employee ID"}
            },
            "required": ["start_date", "end_date"]
        }
    },
    "search_sales_orders": {
        "name": "search_sales_orders",
        "description": "Search sales orders with advanced filters", 
        "inputSchema": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "properties": {
                        "date_from": {"type": "string"},
                        "date_to": {"type": "string"},
                        "partner_id": {"type": "integer"},
                        "state": {"type": "string"},
                        "limit": {"type": "integer", "default": 20}
                    }
                }
            },
            "required": ["filters"]
        }
    },
    "create_sales_order": {
        "name": "create_sales_order",
        "description": "Create a new sales order",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order": {
                    "type": "object",
                    "properties": {
                        "partner_id": {"type": "integer"},
                        "order_lines": {"type": "array"}
                    }
                }
            },
            "required": ["order"]
        }
    },
    "analyze_sales_performance": {
        "name": "analyze_sales_performance",
        "description": "Analyze sales performance in a period",
        "inputSchema": {
            "type": "object",
            "properties": {
                "params": {
                    "type": "object",
                    "properties": {
                        "date_from": {"type": "string"},
                        "date_to": {"type": "string"},
                        "group_by": {"type": "string"}
                    }
                }
            },
            "required": ["params"]
        }
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan handler"""
    logger.info("Starting Odoo MCP HTTP Server...")
    yield
    logger.info("Stopping Odoo MCP HTTP Server...")

# Create FastAPI app
app = FastAPI(
    title="Odoo MCP Server",
    description="HTTP/SSE MCP Server for Odoo Integration - n8n Compatible",
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
    return {
        "status": "healthy", 
        "service": "odoo-mcp-server",
        "version": "1.1.0"
    }

@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "service": "Odoo MCP Server",
        "version": "1.1.0",
        "transport": "HTTP/SSE",
        "compatibility": "n8n MCP Client",
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
    """Process MCP request with n8n compatibility"""
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
            tools_list = []
            for tool_name, tool_config in AVAILABLE_TOOLS.items():
                tools_list.append({
                    "name": tool_config["name"],
                    "description": tool_config["description"],
                    "inputSchema": tool_config["inputSchema"]
                })
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools_list
                }
            }
            
        elif method == "resources/list":
            resources = [
                {
                    "uri": "odoo://models",
                    "name": "Odoo Models",
                    "description": "List all available models in the Odoo system",
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
            
            if tool_name not in AVAILABLE_TOOLS:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
            else:
                try:
                    # Create mock context
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
                    
                    # Call the appropriate function
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
                    else:
                        raise ValueError(f"Tool implementation not found: {tool_name}")
                    
                    # Format response for n8n MCP Client
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

@app.get("/sse")
@app.post("/sse")
async def handle_sse_mcp(request: Request):
    """Handle MCP requests via Server-Sent Events - n8n Compatible
    
    Supports both GET (for SSE connection) and POST (for messages)
    """
    method = request.method
    logger.info(f"SSE connection: {method}")
    
    async def event_generator():
        try:
            body = await request.body()
            if body:
                # POST with body - process the request
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
            else:
                # GET or empty POST - send handshake only
                handshake = {
                    "type": "handshake",
                    "serverInfo": {
                        "name": "odoo-mcp-server",
                        "version": "1.1.0"
                    },
                    "capabilities": {
                        "tools": True,
                        "resources": True
                    }
                }
                yield f"data: {json.dumps(handshake)}\n\n"
            
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
    """Handle MCP requests via standard HTTP POST - n8n Compatible"""
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
    
    logger.info(f"Starting n8n-compatible MCP server on {host}:{port}")
    logger.info("Environment check:")
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
