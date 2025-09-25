# Odoo MCP Remote Server - Dynamic Authentication

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A powerful Model Context Protocol (MCP) server for Odoo integration with **dynamic per-request authentication**. Perfect for multi-tenant deployments and SaaS environments where each client needs to connect to their own Odoo instance.

## 🚀 Key Features

- **🔐 Dynamic Authentication**: Each request can use different Odoo credentials
- **🌐 Multi-Tenant Ready**: One server, multiple Odoo instances
- **📡 n8n Compatible**: Designed to work seamlessly with n8n workflows
- **🛡️ Secure**: No credentials stored on the server
- **⚡ FastAPI Backend**: High-performance async API
- **🔄 Flexible Authentication**: Multiple ways to send credentials

## 🏗️ Architecture

```
┌─────────────┐    HTTP + Auth    ┌──────────────────┐    XML-RPC    ┌─────────────┐
│ n8n Client  │ ─────────────────► │ MCP Remote      │ ─────────────► │ Odoo A      │
│ (Tenant A)  │   Headers/Body     │ Server          │               │ Instance    │
└─────────────┘                    │                 │               └─────────────┘
                                   │                 │
┌─────────────┐    HTTP + Auth    │                 │    XML-RPC    ┌─────────────┐
│ n8n Client  │ ─────────────────► │                 │ ─────────────► │ Odoo B      │
│ (Tenant B)  │   Headers/Body     │                 │               │ Instance    │
└─────────────┘                    └──────────────────┘               └─────────────┘
```

## 📝 Authentication Methods

### Method 1: HTTP Headers (Recommended for n8n)

```http
POST /mcp
Content-Type: application/json
x-odoo-url: https://tenant-a.odoo.com
x-odoo-db: production
x-odoo-username: api_user
x-odoo-password: secure_password

{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_sales_orders",
    "arguments": {"filters": {"limit": 10}}
  },
  "id": 1
}
```

### Method 2: Request Body

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_sales_orders",
    "arguments": {"filters": {"limit": 10}}
  },
  "odoo_credentials": {
    "url": "https://tenant-a.odoo.com",
    "db": "production", 
    "username": "api_user",
    "password": "secure_password"
  },
  "id": 1
}
```

### Method 3: Environment Variables (Fallback)

```env
ODOO_URL=https://default.odoo.com
ODOO_DB=default_db
ODOO_USERNAME=default_user
ODOO_PASSWORD=default_pass
```

## 🚀 Deployment

### Docker Deployment

```bash
# Clone the repository
git clone https://github.com/frescales/odoo-mcp-improved.git
cd odoo-mcp-improved
git checkout odoo-remote-server

# Build and run
docker build -f Dockerfile.http -t odoo-mcp-remote .
docker run -p 8000:8000 odoo-mcp-remote
```

### EasyPanel Deployment

1. **Create new service in EasyPanel**
2. **Configure source:**
   - Repository: `frescales/odoo-mcp-improved`
   - Branch: `odoo-remote-server`
   - Dockerfile: `Dockerfile.http`
3. **Environment variables (optional fallback):**
   ```env
   PORT=8000
   # Optional default credentials (fallback only)
   ODOO_URL=https://default.odoo.com
   ODOO_DB=default_db
   ODOO_USERNAME=default_user
   ODOO_PASSWORD=default_pass
   ```

## 🔧 n8n Configuration

### Step 1: Add MCP Node
Add an "MCP" node to your n8n workflow.

### Step 2: Configure Connection
- **Endpoint**: `https://your-server.com/mcp`
- **Transport**: `HTTP Streamable`
- **Authentication**: `None` (we handle auth dynamically)

### Step 3: Configure Headers
In n8n's MCP node, add these headers:

| Header Name | Value | Description |
|-------------|--------|-------------|
| `x-odoo-url` | `https://your-odoo.com` | Odoo server URL |
| `x-odoo-db` | `your_database` | Database name |
| `x-odoo-username` | `your_username` | Odoo username |
| `x-odoo-password` | `your_password` | Odoo password |

### Step 4: Use Dynamic Values
You can make headers dynamic using n8n expressions:
```javascript
{
  "x-odoo-url": "{{ $json.odoo_config.url }}",
  "x-odoo-db": "{{ $json.odoo_config.database }}",
  "x-odoo-username": "{{ $json.odoo_config.username }}",  
  "x-odoo-password": "{{ $json.odoo_config.password }}"
}
```

## 📡 API Endpoints

### Core Endpoints
- `POST /mcp` - Main MCP endpoint (standard HTTP)
- `POST /sse` - MCP endpoint with Server-Sent Events
- `GET /health` - Health check
- `GET /` - Server information and supported authentication methods

### Example Usage

**Check server health:**
```bash
curl https://your-server.com/health
```

**Test authentication:**
```bash
curl -X POST https://your-server.com/mcp \
  -H "Content-Type: application/json" \
  -H "x-odoo-url: https://demo.odoo.com" \
  -H "x-odoo-db: demo" \
  -H "x-odoo-username: admin" \
  -H "x-odoo-password: admin" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

## 🛠️ Available Tools

The server supports all original Odoo MCP tools:

### Sales & CRM
- `search_sales_orders` - Search and filter sales orders
- `create_sales_order` - Create new sales orders  
- `analyze_sales_performance` - Sales analytics

### Purchasing
- `search_purchase_orders` - Search purchase orders
- `create_purchase_order` - Create purchase orders
- `analyze_supplier_performance` - Supplier analytics

### Inventory
- `check_product_availability` - Stock levels
- `create_inventory_adjustment` - Stock adjustments
- `analyze_inventory_turnover` - Inventory analytics

### HR & General
- `search_employee` - Find employees
- `search_holidays` - Employee leave management
- `execute_method` - Execute any Odoo model method

## 🔒 Security Considerations

- **No Credential Storage**: Server never stores credentials persistently
- **Per-Request Authentication**: Each request is authenticated independently  
- **HTTPS Recommended**: Always use HTTPS in production
- **Header Security**: Credentials in headers are only visible during request
- **Audit Trail**: All authentication attempts are logged (without passwords)

## 🚨 Troubleshooting

### Common Issues

**1. Authentication Failed**
```json
{
  "error": {
    "code": -32602,
    "message": "Missing Odoo credentials"
  }
}
```
**Solution**: Ensure you're sending credentials via headers or request body.

**2. Invalid Credentials**
```json
{
  "error": {
    "code": -32603,
    "message": "Tool execution failed: Authentication failed"
  }
}
```
**Solution**: Verify your Odoo credentials are correct and the user has API access.

**3. Connection Timeout**
```json
{
  "error": {
    "message": "Failed to connect to Odoo server: timeout"
  }
}
```
**Solution**: Check if the Odoo URL is accessible and not behind a firewall.

### Debugging

**Check server status:**
```bash
curl https://your-server.com/health
```

**Test with demo credentials:**
```bash
curl -X POST https://your-server.com/mcp \
  -H "Content-Type: application/json" \
  -H "x-odoo-url: https://demo.odoo.com" \
  -H "x-odoo-db: demo" \
  -H "x-odoo-username: admin" \
  -H "x-odoo-password: admin" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

## 🌟 Usage Examples

### Multi-Tenant Setup

```python
# Tenant A workflow
headers_a = {
    "x-odoo-url": "https://tenant-a.odoo.com",
    "x-odoo-db": "production",
    "x-odoo-username": "api_user_a",
    "x-odoo-password": "password_a"
}

# Tenant B workflow  
headers_b = {
    "x-odoo-url": "https://tenant-b.odoo.com", 
    "x-odoo-db": "main",
    "x-odoo-username": "api_user_b",
    "x-odoo-password": "password_b"
}
```

### Dynamic Credential Loading in n8n

```javascript
// In n8n, you can load credentials from previous nodes
const odooConfig = $node["Get Tenant Config"].json;

return {
  headers: {
    "x-odoo-url": odooConfig.odoo_url,
    "x-odoo-db": odooConfig.database,
    "x-odoo-username": odooConfig.api_user,
    "x-odoo-password": odooConfig.api_password
  }
};
```

## 📊 Monitoring

The server includes comprehensive logging:

```bash
# Authentication attempts (without passwords)
2024-09-25 10:30:15 - INFO - Processing MCP request: tools/call
2024-09-25 10:30:16 - INFO - Connecting to Odoo at: https://tenant-a.odoo.com
2024-09-25 10:30:17 - INFO - Authentication successful for: api_user_a

# Errors
2024-09-25 10:35:20 - WARNING - Missing Odoo credentials: ['password']
2024-09-25 10:40:30 - ERROR - Failed to create Odoo client: Authentication failed
```

## 🔄 Migration from Static Version

If you're migrating from the static authentication version:

1. **Update your deployment** to use the `odoo-remote-server` branch
2. **Remove environment variables** from your server configuration
3. **Update n8n workflows** to include authentication headers
4. **Test thoroughly** with your existing Odoo instances

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch from `odoo-remote-server`
3. Make your changes
4. Test with multiple Odoo instances
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the original [odoo-mcp-improved](https://github.com/hachecito/odoo-mcp-improved)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- Designed for [n8n](https://n8n.io/) workflows

---

**🎯 Perfect for:**
- Multi-tenant SaaS applications
- Dynamic Odoo integrations  
- Secure credential handling
- n8n workflow automation
- Enterprise deployments

**Need help?** Create an issue or check the [main documentation](README.md).
