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

## 📝 n8n Authentication Methods

### Method 1: Header Auth - Single Header (Recommended)

The simplest way to authenticate with n8n using a single header containing JSON credentials.

#### Configuration in n8n:
1. **Add MCP Client node** to your workflow
2. **Set Authentication** to "Header Auth account"
3. **Configure the Header Auth account**:

| Field | Value |
|-------|--------|
| **Name** | `x-auth-credentials` |
| **Value** | `{"url":"https://your-company.odoo.com","db":"your_database","username":"your_username","password":"your_password"}` |

#### Example configuration:
```
Name: x-auth-credentials
Value: {"url":"https://mycompany.odoo.com","db":"production","username":"api_user","password":"secure_password"}
```

### Method 2: Header Auth - Bearer Token

Use a Bearer token with base64-encoded credentials.

#### Configuration in n8n:
| Field | Value |
|-------|--------|
| **Name** | `Authorization` |
| **Value** | `Bearer <base64_encoded_json>` |

#### Generate Bearer Token:
To create the Bearer token for your credentials:

1. **Take your credentials JSON**:
```json
{"url":"https://your-company.odoo.com","db":"your_database","username":"your_username","password":"your_password"}
```

2. **Encode in base64** and add Bearer prefix:
```
Bearer eyJ1cmwiOiJodHRwczovL3lvdXItY29tcGFueS5vZG9vLmNvbSIsImRiIjoieW91cl9kYXRhYmFzZSIsInVzZXJuYW1lIjoieW91cl91c2VybmFtZSIsInBhc3N3b3JkIjoieW91cl9wYXNzd29yZCJ9
```

### Method 3: Custom Auth (Alternative)

For multiple headers, use Custom Auth instead.

#### Configuration in n8n:
```json
{
  "headers": {
    "odoo_url": "https://your-company.odoo.com",
    "odoo_db": "your_database",
    "odoo_username": "your_username",
    "odoo_password": "your_password"
  }
}
```

## 🚀 Deployment

### Docker Deployment

```bash
# Clone the repository
git clone https://github.com/frescales/odoo-mcp-improved.git
cd odoo-mcp-improved
git checkout odoo-remote-clean

# Build and run
docker build -f Dockerfile.remote -t odoo-mcp-remote .
docker run -p 8000:8000 odoo-mcp-remote
```

### EasyPanel Deployment

1. **Create new service in EasyPanel**
2. **Configure source:**
   - Repository: `frescales/odoo-mcp-improved`
   - Branch: `odoo-remote-clean`
   - Dockerfile: `Dockerfile.remote`
3. **Environment variables (optional fallback):**
   ```env
   PORT=8000
   # Optional default credentials (fallback only)
   ODOO_URL=https://default.odoo.com
   ODOO_DB=default_db
   ODOO_USERNAME=default_user
   ODOO_PASSWORD=default_pass
   ```

## 🔧 n8n Setup Guide

### Complete n8n Configuration:

1. **Add MCP Client node** to your n8n workflow

2. **Configure connection parameters**:
   - **Endpoint**: `https://your-server.com/mcp`
   - **Server Transport**: `HTTP Streamable`
   - **Authentication**: `Header Auth account`
   - **Tools to Include**: `All`
   - **Timeout**: `60000`

3. **Create Header Auth account**:
   - **Name**: `x-auth-credentials`
   - **Value**: Your Odoo credentials as JSON (see examples above)

4. **Test the connection** by calling `tools/list`

### Working Example with Demo Server:

Here's a complete working configuration using Odoo's demo instance:

**MCP Node Settings:**
- Endpoint: `https://your-mcp-server.com/mcp`
- Transport: `HTTP Streamable`
- Authentication: Header Auth account named "Odoo Demo"

**Header Auth Account "Odoo Demo":**
- Name: `x-auth-credentials`
- Value: `{"url":"https://demo.odoo.com","db":"demo","username":"admin","password":"admin"}`

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

**Test with Header Auth format:**
```bash
curl -X POST https://your-server.com/mcp \
  -H "Content-Type: application/json" \
  -H "x-auth-credentials: {\"url\":\"https://demo.odoo.com\",\"db\":\"demo\",\"username\":\"admin\",\"password\":\"admin\"}" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

**Test with Bearer token:**
```bash
curl -X POST https://your-server.com/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ1cmwiOiJodHRwczovL2RlbW8ub2Rvby5jb20iLCJkYiI6ImRlbW8iLCJ1c2VybmFtZSI6ImFkbWluIiwicGFzc3dvcmQiOiJhZG1pbiJ9" \
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
**Solution**: Ensure you're sending credentials via the correct header format.

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

**3. JSON Format Error in Header Auth**
**Solution**: Ensure your JSON in the header value is properly formatted with escaped quotes if needed.

### Debugging

**Check server status:**
```bash
curl https://your-server.com/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "odoo-mcp-remote-server",
  "version": "2.1.0",
  "authentication": "dynamic",
  "n8n_compatible": true
}
```

## 🌟 Real-World Example

### Multi-Tenant SaaS Setup

```javascript
// In your n8n workflow, you can switch between different Odoo instances
const tenants = {
  "company_a": {
    "url": "https://company-a.odoo.com",
    "db": "production",
    "username": "api_user",
    "password": "secure_password_a"
  },
  "company_b": {
    "url": "https://company-b.odoo.com", 
    "db": "main",
    "username": "integration_user",
    "password": "secure_password_b"
  }
};

// Use different credentials based on context
const selectedTenant = tenants[$json.tenant_id];
const authHeader = JSON.stringify(selectedTenant);

// This goes in your Header Auth configuration
```

## 🔄 Migration from Static Version

If you're migrating from the static authentication version:

1. **Update your deployment** to use the `odoo-remote-clean` branch
2. **Remove environment variables** from your server configuration  
3. **Update n8n workflows** to include authentication headers
4. **Test thoroughly** with your existing Odoo instances

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch from `odoo-remote-clean`
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

**Need help?** Check the [troubleshooting section](#troubleshooting) or create an issue in the repository.
