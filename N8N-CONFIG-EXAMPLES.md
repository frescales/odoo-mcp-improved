# n8n Configuration Example for Odoo MCP Remote Server

This document shows how to configure n8n to use the Odoo MCP Remote Server with dynamic authentication.

## MCP Node Configuration

### Basic Setup
1. Add an "MCP" node to your workflow
2. Set these connection parameters:

```json
{
  "endpoint": "https://your-server.com/mcp",
  "transport": "HTTP Streamable",
  "authentication": "None"
}
```

### Authentication Headers

Configure these headers in the MCP node:

#### Static Credentials
```json
{
  "x-odoo-url": "https://your-odoo.com",
  "x-odoo-db": "your_database", 
  "x-odoo-username": "your_username",
  "x-odoo-password": "your_password"
}
```

#### Dynamic Credentials (Recommended)
```javascript
// Use expressions to load credentials from previous nodes
{
  "x-odoo-url": "{{ $json.odoo_config.url }}",
  "x-odoo-db": "{{ $json.odoo_config.database }}",
  "x-odoo-username": "{{ $json.odoo_config.username }}",
  "x-odoo-password": "{{ $json.odoo_config.password }}"
}
```

## Example Workflows

### 1. Multi-Tenant Sales Report

```json
{
  "nodes": [
    {
      "name": "Get Tenant Config",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {
          "string": [
            {
              "name": "tenant_id",
              "value": "tenant_a"
            },
            {
              "name": "odoo_url", 
              "value": "https://tenant-a.odoo.com"
            },
            {
              "name": "odoo_db",
              "value": "production"
            },
            {
              "name": "odoo_user",
              "value": "api_user"
            },
            {
              "name": "odoo_password",
              "value": "secure_password"
            }
          ]
        }
      }
    },
    {
      "name": "Get Sales Orders",
      "type": "mcp",
      "parameters": {
        "endpoint": "https://your-mcp-server.com/mcp",
        "transport": "HTTP Streamable",
        "method": "tools/call",
        "params": {
          "name": "search_sales_orders",
          "arguments": {
            "filters": {
              "limit": 50,
              "date_from": "2024-01-01",
              "state": "sale"
            }
          }
        }
      },
      "headers": {
        "x-odoo-url": "={{ $node['Get Tenant Config'].json.odoo_url }}",
        "x-odoo-db": "={{ $node['Get Tenant Config'].json.odoo_db }}",
        "x-odoo-username": "={{ $node['Get Tenant Config'].json.odoo_user }}",
        "x-odoo-password": "={{ $node['Get Tenant Config'].json.odoo_password }}"
      }
    }
  ]
}
```

### 2. Dynamic Employee Search

```json
{
  "name": "Search Employee",
  "type": "mcp", 
  "parameters": {
    "endpoint": "https://your-mcp-server.com/mcp",
    "method": "tools/call",
    "params": {
      "name": "search_employee",
      "arguments": {
        "name": "={{ $json.employee_name }}",
        "limit": 10
      }
    }
  },
  "headers": {
    "x-odoo-url": "{{ $json.client_config.odoo_url }}",
    "x-odoo-db": "{{ $json.client_config.database }}",
    "x-odoo-username": "{{ $json.client_config.api_user }}",
    "x-odoo-password": "{{ $json.client_config.api_password }}"
  }
}
```

### 3. Create Sales Order with Authentication

```json
{
  "name": "Create Order",
  "type": "mcp",
  "parameters": {
    "endpoint": "https://your-mcp-server.com/mcp", 
    "method": "tools/call",
    "params": {
      "name": "create_sales_order",
      "arguments": {
        "order": {
          "partner_id": 1,
          "order_lines": [
            {
              "product_id": 1,
              "quantity": 2,
              "price_unit": 100.0
            }
          ]
        }
      }
    }
  },
  "headers": {
    "x-odoo-url": "https://client.odoo.com",
    "x-odoo-db": "main",
    "x-odoo-username": "sales_api",
    "x-odoo-password": "api_key_here"
  }
}
```

## Advanced Patterns

### Credential Rotation
```javascript
// Rotate credentials based on time or other factors
const currentHour = new Date().getHours();
const credentialSet = currentHour < 12 ? 'morning' : 'evening';

return {
  headers: {
    "x-odoo-url": $json.credentials[credentialSet].url,
    "x-odoo-db": $json.credentials[credentialSet].database,
    "x-odoo-username": $json.credentials[credentialSet].username,
    "x-odoo-password": $json.credentials[credentialSet].password
  }
};
```

### Error Handling
```javascript
// Handle authentication errors gracefully
if ($json.error && $json.error.code === -32602) {
  // Missing credentials error
  return {
    error: "Authentication failed - check credentials",
    retry_with_backup: true
  };
}
```

### Batch Operations
```javascript
// Process multiple tenants in sequence
const tenants = $json.tenants;
const results = [];

for (const tenant of tenants) {
  const headers = {
    "x-odoo-url": tenant.odoo_url,
    "x-odoo-db": tenant.database, 
    "x-odoo-username": tenant.username,
    "x-odoo-password": tenant.password
  };
  
  // Process each tenant with their own credentials
  results.push({
    tenant_id: tenant.id,
    headers: headers
  });
}

return results;
```

## Testing Configuration

### Test Connection
```bash
curl -X POST https://your-mcp-server.com/mcp \
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

### Validate Headers in n8n
Add a debug node to check your headers:
```javascript
return {
  headers_sent: $node["MCP"].headers,
  response_received: $json
};
```

## Security Best Practices

1. **Use HTTPS**: Always use secure connections
2. **Rotate Credentials**: Implement credential rotation
3. **Limit Permissions**: Use dedicated API users with minimal permissions
4. **Monitor Usage**: Track API usage per tenant
5. **Rate Limiting**: Implement rate limiting per client

## Common Issues

### Missing Headers
- **Problem**: Headers not being sent
- **Solution**: Verify header configuration in MCP node

### Invalid Credentials
- **Problem**: Authentication fails
- **Solution**: Test credentials directly with Odoo API first

### Connection Timeout
- **Problem**: Requests timing out
- **Solution**: Check network connectivity and increase timeout

## Support

For more examples and support:
- Check the [main documentation](README-REMOTE.md)
- Review server logs for authentication details
- Test with `/health` endpoint first
