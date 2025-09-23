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
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from mcp.server.sse import SseServerTransport
from mcp.server.lowlevel import Server

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
    version="1.0.0",
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
    return {"status": "healthy", "service": "odoo-mcp-server"}

@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "service": "Odoo MCP Server",
        "version": "1.0.0",
        "transport": "HTTP/SSE",
        "endpoints": {
            "health": "/health",
            "mcp": "/sse",
            "docs": "/docs"
        },
        "environment": {
            "odoo_url": os.getenv("ODOO_URL", "not_configured"),
            "odoo_db": os.getenv("ODOO_DB", "not_configured"),
            "odoo_username": os.getenv("ODOO_USERNAME", "not_configured")
        }
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
            # Create SSE transport
            transport = SseServerTransport("/sse")
            
            # Get the FastMCP server from odoo_mcp_server
            mcp_server = odoo_mcp_server._mcp_server
            
            # Create a simple request/response handler
            async def handle_request(request_data):
                try:
                    # Process the MCP request
                    response = await mcp_server._handle_request(request_data)
                    return response
                except Exception as e:
                    logger.error(f"Error handling MCP request: {e}")
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        },
                        "id": request_data.get("id")
                    }
            
            # Read request body
            body = await request.body()
            if body:
                try:
                    request_data = json.loads(body.decode())
                    response = await handle_request(request_data)
                    
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
        
        # Get the FastMCP server
        mcp_server = odoo_mcp_server._mcp_server
        
        # Process the request
        response = await mcp_server._handle_request(request_data)
        
        return response
        
    except json.JSONDecodeError as e:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            },
            "id": request_data.get("id") if 'request_data' in locals() else None
        }
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            "id": request_data.get("id") if 'request_data' in locals() else None
        }

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
