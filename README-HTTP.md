# Odoo MCP Server - HTTP/SSE Version

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A powerful Model Context Protocol (MCP) server for Odoo integration, redesigned to work via HTTP/Server-Sent Events (SSE) for remote deployment and n8n integration.

## 🚀 Features

- **HTTP/SSE Transport**: Works remotely via HTTP instead of stdio
- **n8n Compatible**: Designed to work with n8n's MCP client tool
- **Flexible Authentication**: Supports both password and API key authentication
- **EasyPanel Ready**: Optimized for EasyPanel deployment
- **Complete Odoo Integration**: All original MCP tools and resources
- **FastAPI Backend**: Modern, fast, and well-documented API
- **Health Monitoring**: Built-in health check endpoints
- **Docker Support**: Ready-to-deploy container

## 🏗️ Architecture

```
┌─────────────┐    HTTP/SSE    ┌──────────────────┐    XML-RPC    ┌─────────────┐
│     n8n     │ ──────────────► │ MCP HTTP Server  │ ─────────────► │    Odoo     │
│ MCP Client  │                │  (FastAPI)       │               │  Instance   │
└─────────────┘                └──────────────────┘               └─────────────┘
```

## 📦 Installation & Deployment

### Option 1: EasyPanel Deployment

1. **Fork this repository** (already done ✅)

2. **In EasyPanel, create a new service:**
   - Choose "GitHub" as source
   - Select your fork: `frescales/odoo-mcp-improved`
   - Branch: `http-server`
   - Dockerfile: `Dockerfile.http`

3. **Configure environment variables:**
   ```env
   ODOO_URL=https://your-odoo-instance.com
   ODOO_DB=your_database_name
   ODOO_USERNAME=your_odoo_username
   
   # Authentication Method 1: Password (traditional)
   ODOO_PASSWORD=your_odoo_password
   
   # Authentication Method 2: API Key (recommended)
   # ODOO_API_KEY=your_api_key_here
   
   PORT=8000
   ```
   
   **🔑 API Key vs Password Authentication:**
   - **API Key (Recommended)**: More secure, can be revoked independently without changing password
   - **Password**: Traditional authentication method
   - **Priority**: If both are set, API Key takes priority
   - **Generate API Keys**: In Odoo go to Settings > Users > Your User > Preferences > API Keys

4. **Deploy and test:**
   - Your server will be available at: `https://your-app.easypanel.host`
   - Health check: `https://your-app.easypanel.host/health`

### Option 2: Local Development

1. **Clone your fork:**
   ```bash
   git clone https://github.com/frescales/odoo-mcp-improved.git
   cd odoo-mcp-improved
   git checkout http-server
   ```

2. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Odoo credentials (use either password or api_key)
   ```

3. **Run with Docker:**
   ```bash
   docker-compose up --build
   ```

4. **Or run directly:**
   ```bash
   pip install -e .
   python app.py
   ```

## 🔐 Authentication Methods

This server supports two authentication methods:

### Method 1: Password Authentication
```env
ODOO_URL=https://your-odoo.com
ODOO_DB=your_database
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password
```

### Method 2: API Key Authentication (Recommended)
```env
ODOO_URL=https://your-odoo.com
ODOO_DB=your_database
ODOO_USERNAME=admin
ODOO_API_KEY=your_api_key_here
```

**How to generate an API Key in Odoo:**
1. Log in to your Odoo instance
2. Go to **Settings** > **Users & Companies** > **Users**
3. Select your user
4. Go to **Preferences** tab
5. Scroll to **API Keys** section
6. Click **New API Key**
7. Give it a description and copy the generated key
8. Use this key in your `ODOO_API_KEY` environment variable

**Why use API Keys?**
- ✅ More secure than passwords
- ✅ Can be revoked independently
- ✅ Can have specific scopes/permissions
- ✅ No need to expose actual password
- ✅ Easier to rotate credentials

## 🔧 n8n Integration

Once deployed, configure n8n to use your MCP server:

1. **Install MCP Client Tool in n8n**
2. **Configure the MCP connection:**
   - **URL**: `https://your-deployed-server.com/sse`
   - **Transport**: `HTTP/SSE`
   - **Method**: `POST`

3. **Test the connection** using the health endpoint

## 📡 API Endpoints

### Core Endpoints
- `GET /` - Server information and status
- `GET /health` - Health check endpoint
- `POST /sse` - Main MCP endpoint (Server-Sent Events)
- `POST /mcp` - Alternative MCP endpoint (standard HTTP)
- `GET /docs` - FastAPI automatic documentation

### Example Usage

**Health Check:**
```bash
curl https://your-server.com/health
```

**Get Server Info:**
```bash
curl https://your-server.com/
```

**MCP Request (via curl):**
```bash
curl -X POST https://your-server.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

## 🛠️ Available MCP Tools

The server includes all original Odoo MCP tools:

### Sales & CRM
- `search_sales_orders` - Search and filter sales orders
- `create_sales_order` - Create new sales orders
- `analyze_sales_performance` - Sales analytics and reporting

### Purchasing
- `search_purchase_orders` - Search purchase orders
- `create_purchase_order` - Create purchase orders
- `analyze_supplier_performance` - Supplier analytics

### Inventory Management
- `check_product_availability` - Stock level verification
- `create_inventory_adjustment` - Stock adjustments
- `analyze_inventory_turnover` - Inventory analytics

### Accounting & Finance
- `search_journal_entries` - Find accounting entries
- `create_journal_entry` - Create accounting entries
- `analyze_financial_ratios` - Financial analysis

### HR & Employees
- `search_employee` - Find employees
- `search_holidays` - Employee leave management

### Generic Tools
- `execute_method` - Execute any Odoo model method

## 🔒 Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `ODOO_URL` | Odoo instance URL | ✅ | `https://mycompany.odoo.com` |
| `ODOO_DB` | Database name | ✅ | `mycompany` |
| `ODOO_USERNAME` | Odoo username | ✅ | `admin` |
| `ODOO_PASSWORD` | Odoo password | ⚠️ | `your_password` |
| `ODOO_API_KEY` | Odoo API Key (recommended) | ⚠️ | `your_api_key` |
| `HOST` | Server host | ❌ | `0.0.0.0` (default) |
| `PORT` | Server port | ❌ | `8000` (default) |
| `ODOO_TIMEOUT` | Connection timeout (seconds) | ❌ | `30` (default) |
| `ODOO_VERIFY_SSL` | Verify SSL certificates | ❌ | `true` (default) |
| `LOG_LEVEL` | Logging level | ❌ | `INFO` (default) |

⚠️ **Note**: Either `ODOO_PASSWORD` or `ODOO_API_KEY` must be provided. If both are set, `ODOO_API_KEY` takes priority.

## 🚨 Security Considerations

- **Never expose credentials** in your repository
- **Use environment variables** for all sensitive data
- **Prefer API Keys** over passwords for better security
- **Configure CORS** appropriately for production
- **Use HTTPS** in production deployments
- **Consider API rate limiting** for public endpoints
- **Rotate API keys** regularly
- **Use separate API keys** for different environments (dev, staging, prod)

## 🐛 Troubleshooting

### Common Issues

1. **Connection refused to Odoo:**
   - Verify `ODOO_URL` is correct and accessible
   - Check Odoo credentials (password or API key)
   - Ensure Odoo allows external API access

2. **Authentication failed:**
   - Verify your API key is active in Odoo
   - Check that the username matches the API key owner
   - Try using password authentication to isolate the issue

3. **n8n can't connect:**
   - Verify the server is running and accessible
   - Check the SSE endpoint URL
   - Review CORS settings

4. **Health check fails:**
   - Check if all environment variables are set
   - Verify Odoo connection
   - Review server logs

### Debugging

**View logs:**
```bash
# Docker
docker-compose logs -f

# Direct run
python app.py
```

**Test Odoo connection:**
```bash
curl -X POST https://your-server.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "resources/list"
  }'
```

## 📈 Monitoring

The server includes built-in monitoring capabilities:

- **Health endpoint**: `/health` - Returns server status
- **Metrics endpoint**: `/` - Shows configuration and status
- **Structured logging**: JSON formatted logs for easy parsing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original project by [hachecito](https://github.com/hachecito/odoo-mcp-improved)
- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)

---

**Need help?** Create an issue in this repository or check the [original documentation](DOCUMENTATION.md).
