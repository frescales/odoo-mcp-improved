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
    # Initialize the MCP server context
    try:
        # Test Odoo connection
        logger.info("Testing Odoo connection...")
        # The actual connection test will happen when first tool is called
        yield
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    finally:
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
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Basic health check
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
        # Get the underlying MCP server
        mcp_server = odoo_mcp_server._mcp_server
        
        # Handle the request based on method
        method = request_data.get("method", "")
        params = request_data.get("params", {})
        request_id = request_data.get("id")
        
        logger.info(f"Processing MCP request: {method}")
        
        if method == "initialize":
            # Handle initialization
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
            # Get available tools from FastMCP
            tools = []
            for tool_name, tool_info in odoo_mcp_server._tools.items():
                tools.append({
                    "name": tool_name,
                    "description": tool_info.get("description", ""),
                    "inputSchema": tool_info.get("parameters", {})
                })
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools}
            }
            
        elif method == "resources/list":
            # Get available resources from FastMCP
            resources = []
            for resource_name, resource_info in odoo_mcp_server._resources.items():
                resources.append({
                    "uri": resource_name,
                    "name": resource_name,
                    "description": resource_info.get("description", ""),
                    "mimeType": "application/json"
                })
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"resources": resources}
            }
            
        elif method == "tools/call":
            # Call a specific tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name in odoo_mcp_server._tools:
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
                    
                    # Get and call the tool function
                    tool_func = odoo_mcp_server._tools[tool_name]["func"]
                    result = tool_func(ctx, **arguments)
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, indent=2)
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
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
                
        elif method == "resources/read":
            # Read a specific resource
            uri = params.get("uri")
            
            if uri in odoo_mcp_server._resources:
                try:
                    # Get and call the resource function
                    resource_func = odoo_mcp_server._resources[uri]["func"]
                    result = resource_func()
                    
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
                        "message": f"Resource not found: {uri}"
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
    """
    Handle MCP requests via Server-Sent Events
    This endpoint is compatible with n8n MCP client tool
    """
    logger.info("New SSE MCP connection")
    
    async def event_generator():
        try:
            # Read request body
            body = await request.body()
            if body:
                try:
                    request_data = json.loads(body.decode())
                    response = await process_mcp_request(request_data)
                    
                    # Send response as SSE event
                    yield f"data: {json.dumps(response)}\n\n"
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        },
                        "id": None
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
            
            # Keep connection alive
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            
        except Exception as e:
            logger.error(f"SSE connection error: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Connection error: {str(e)}"
                },
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
    """
    Handle MCP requests via standard HTTP POST
    Alternative endpoint for non-SSE clients
    """
    try:
        # Get request body
        body = await request.body()
        request_data = json.loads(body.decode())
        
        # Process the request
        response = await process_mcp_request(request_data)
        
        return JSONResponse(content=response)
        
    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                },
                "id": None
            }
        )
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": request_data.get("id") if 'request_data' in locals() else None
            }
        )

if __name__ == "__main__":
    # Configuration from environment variables
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
