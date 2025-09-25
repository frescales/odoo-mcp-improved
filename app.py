#!/usr/bin/env python
"""
HTTP/SSE MCP Server for Odoo Integration with Dynamic Authentication
Compatible with n8n MCP Client node - supports per-request authentication
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from src.odoo_mcp.server import mcp as odoo_mcp_server
from src.odoo_mcp.odoo_client import OdooClient

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

def extract_odoo_credentials(request_data: Dict[str, Any], headers: Dict[str, str]) -> Optional[Dict[str, str]]:
    """
    Extract Odoo credentials from request data or headers
    
    Priority:
    1. Request body credentials
    2. HTTP headers
    3. Environment variables (fallback)
    """
    credentials = {}
    
    # Try to get from request body first
    if "odoo_credentials" in request_data:
        creds = request_data["odoo_credentials"]
        credentials.update({
            "url": creds.get("url"),
            "db": creds.get("db") or creds.get("database"),
            "username": creds.get("username") or creds.get("user"),
            "password": creds.get("password")
        })
    
    # Try to get from headers
    header_mapping = {
        "url": ["x-odoo-url", "odoo-url"],
        "db": ["x-odoo-db", "odoo-db", "x-odoo-database", "odoo-database"],
        "username": ["x-odoo-username", "odoo-username", "x-odoo-user", "odoo-user"],
        "password": ["x-odoo-password", "odoo-password"]
    }
    
    for key, header_options in header_mapping.items():
        if not credentials.get(key):
            for header in header_options:
                if header in headers:
                    credentials[key] = headers[header]
                    break
    
    # Fallback to environment variables
    env_mapping = {
        "url": "ODOO_URL",
        "db": "ODOO_DB", 
        "username": "ODOO_USERNAME",
        "password": "ODOO_PASSWORD"
    }
    
    for key, env_var in env_mapping.items():
        if not credentials.get(key):
            credentials[key] = os.getenv(env_var)
    
    # Validate that we have all required credentials
    required_fields = ["url", "db", "username", "password"]
    if all(credentials.get(field) for field in required_fields):
        return credentials
    
    missing = [field for field in required_fields if not credentials.get(field)]
    logger.warning(f"Missing Odoo credentials: {missing}")
    return None

def create_odoo_client(credentials: Dict[str, str]) -> OdooClient:
    """Create an Odoo client with the provided credentials"""
    try:
        return OdooClient(
            url=credentials["url"],
            db=credentials["db"],
            username=credentials["username"],
            password=credentials["password"],
            timeout=int(os.getenv("ODOO_TIMEOUT", "30")),
            verify_ssl=os.getenv("ODOO_VERIFY_SSL", "1").lower() in ["1", "true", "yes"]
        )
    except Exception as e:
        logger.error(f"Failed to create Odoo client: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan handler"""
    logger.info("Starting Odoo MCP Remote Server...")
    yield
    logger.info("Stopping Odoo MCP Remote Server...")

# Create FastAPI app
app = FastAPI(
    title="Odoo MCP Remote Server",
    description="HTTP/SSE MCP Server for Odoo Integration with Dynamic Authentication - n8n Compatible",
    version="2.0.0",
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
        "service": "odoo-mcp-remote-server",
        "version": "2.0.0",
        "authentication": "dynamic"
    }

@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "service": "Odoo MCP Remote Server",
        "version": "2.0.0",
        "transport": "HTTP/SSE",
        "authentication": "dynamic",
        "compatibility": "n8n MCP Client",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp",
            "sse": "/sse", 
            "docs": "/docs"
        },
        "authentication_methods": [
            "request_body.odoo_credentials",
            "http_headers.x-odoo-*",
            "environment_variables (fallback)"
        ],
        "supported_headers": [
            "x-odoo-url", "x-odoo-db", "x-odoo-username", "x-odoo-password"
        ]
    }

async def process_mcp_request(request_data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Process MCP request with dynamic authentication"""
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
                        "name": "odoo-mcp-remote-server",
                        "version": "2.0.0"
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
            # Extract Odoo credentials
            credentials = extract_odoo_credentials(request_data, headers)
            if not credentials:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Missing Odoo credentials. Please provide credentials in request body or headers.",
                        "data": {
                            "required_fields": ["url", "db", "username", "password"],
                            "supported_methods": [
                                "request_body.odoo_credentials",
                                "headers: x-odoo-url, x-odoo-db, x-odoo-username, x-odoo-password"
                            ]
                        }
                    }
                }
                return response
            
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
                    # Create Odoo client with dynamic credentials
                    odoo_client = create_odoo_client(credentials)
                    
                    # Create mock context with dynamic client
                    class MockContext:
                        class MockRequestContext:
                            class MockLifespanContext:
                                def __init__(self, client):
                                    self.odoo = client
                            
                            def __init__(self, client):
                                self.lifespan_context = self.MockLifespanContext(client)
                        
                        def __init__(self, client):
                            self.request_context = self.MockRequestContext(client)
                    
                    ctx = MockContext(odoo_client)
                    
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
            # Extract Odoo credentials
            credentials = extract_odoo_credentials(request_data, headers)
            if not credentials:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Missing Odoo credentials for resource access"
                    }
                }
                return response
            
            uri = params.get("uri")
            
            try:
                if uri == "odoo://models":
                    odoo_client = create_odoo_client(credentials)
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
    """Handle MCP requests via Server-Sent Events - n8n Compatible with Dynamic Auth"""
    logger.info("New SSE MCP connection")
    
    # Extract headers
    headers = {key.lower(): value for key, value in request.headers.items()}
    
    async def event_generator():
        try:
            body = await request.body()
            if body:
                try:
                    request_data = json.loads(body.decode())
                    response = await process_mcp_request(request_data, headers)
                    yield f"data: {json.dumps(response)}\n\n"
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                        "id": None
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
            else:
                # Send initial handshake for n8n compatibility
                handshake = {
                    "type": "handshake",
                    "serverInfo": {
                        "name": "odoo-mcp-remote-server",
                        "version": "2.0.0"
                    },
                    "capabilities": {
                        "tools": True,
                        "resources": True,
                        "authentication": "dynamic"
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
    """Handle MCP requests via standard HTTP POST - n8n Compatible with Dynamic Auth"""
    try:
        # Extract headers
        headers = {key.lower(): value for key, value in request.headers.items()}
        
        body = await request.body()
        request_data = json.loads(body.decode())
        response = await process_mcp_request(request_data, headers)
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
    
    logger.info(f"Starting n8n-compatible MCP Remote Server on {host}:{port}")
    logger.info("Authentication: DYNAMIC (per-request)")
    logger.info("Supported credential sources:")
    logger.info("  1. Request body: odoo_credentials object")
    logger.info("  2. HTTP headers: x-odoo-url, x-odoo-db, x-odoo-username, x-odoo-password")
    logger.info("  3. Environment variables (fallback)")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
