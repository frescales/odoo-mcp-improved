# n8n Header Auth Setup Guide

Esta guía te mostrará exactamente cómo configurar n8n para usar el servidor MCP con Header Auth, que es el método que estás viendo en las capturas de pantalla.

## 📋 Configuración en n8n

### Paso 1: Configurar el Nodo MCP

En tu workflow de n8n:

1. **Endpoint**: `https://n8n-odoo.e2zone.easypanel.host/mcp`
2. **Server Transport**: `HTTP Streamable` 
3. **Authentication**: `Header Auth account` (como se ve en tu captura)

### Paso 2: Configurar Header Auth Account

Cuando selecciones "Header Auth account", se abrirá el modal de configuración que viste. Aquí debes configurar:

#### Configuración del Header Auth:
- **Name**: `Authorization` (o el nombre que prefieras)
- **Value**: Puedes usar cualquiera de estos formatos:

#### Opción 1: Headers individuales (Recomendado)
Configura múltiples headers en la cuenta de Header Auth:

| Name | Value |
|------|--------|
| `odoo_url` | `https://tu-odoo.com` |
| `odoo_db` | `tu_base_datos` |
| `odoo_username` | `tu_usuario` |
| `odoo_password` | `tu_password` |

#### Opción 2: Un solo header con JSON
- **Name**: `x-auth-credentials`
- **Value**: 
```json
{"url":"https://tu-odoo.com","db":"tu_base_datos","username":"tu_usuario","password":"tu_password"}
```

#### Opción 3: Bearer Token con JSON codificado
- **Name**: `Authorization`
- **Value**: `Bearer <base64_encoded_credentials>`

Para generar el Bearer token:
```javascript
// En n8n, puedes usar esta función para generar el token
const credentials = {
  "url": "https://tu-odoo.com",
  "db": "tu_base_datos", 
  "username": "tu_usuario",
  "password": "tu_password"
};

const token = btoa(JSON.stringify(credentials));
return `Bearer ${token}`;
```

## 🔧 Configuración Recomendada para n8n

### Método Más Simple (Recomendado):

1. **En n8n**, crear una cuenta de "Header Auth"
2. **Agregar estos headers**:

```
Name: odoo_url
Value: https://tu-instancia.odoo.com

Name: odoo_db  
Value: tu_base_datos

Name: odoo_username
Value: tu_usuario_api

Name: odoo_password
Value: tu_password_seguro
```

3. **Guardar la cuenta** y asignarla al nodo MCP

### Usando Variables de n8n:

Si quieres hacer las credenciales dinámicas, puedes usar expresiones de n8n:

```
Name: odoo_url
Value: {{ $json.client_config.odoo_url }}

Name: odoo_db
Value: {{ $json.client_config.database }}

Name: odoo_username  
Value: {{ $json.client_config.api_user }}

Name: odoo_password
Value: {{ $json.client_config.api_password }}
```

## 🧪 Testing de la Configuración

### Prueba Manual con curl:
```bash
curl -X POST https://n8n-odoo.e2zone.easypanel.host/mcp \
  -H "Content-Type: application/json" \
  -H "odoo_url: https://demo.odoo.com" \
  -H "odoo_db: demo" \
  -H "odoo_username: admin" \
  -H "odoo_password: admin" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

### Verificar que el servidor esté funcionando:
```bash
curl https://n8n-odoo.e2zone.easypanel.host/health
```

Deberías recibir:
```json
{
  "status": "healthy",
  "service": "odoo-mcp-remote-server", 
  "version": "2.1.0",
  "authentication": "dynamic",
  "n8n_compatible": true
}
```

## 📝 Ejemplo Completo en n8n

### Workflow de Ejemplo:

1. **Nodo Set** (opcional) - Para configurar credenciales dinámicas:
```json
{
  "odoo_config": {
    "url": "https://mi-empresa.odoo.com",
    "database": "produccion",
    "api_user": "n8n_api",
    "api_password": "password_seguro"
  }
}
```

2. **Nodo MCP** - Configurado con Header Auth:
- **Endpoint**: `https://n8n-odoo.e2zone.easypanel.host/mcp`
- **Authentication**: Header Auth con las credenciales configuradas
- **Method**: `tools/call`
- **Params**:
```json
{
  "name": "search_sales_orders",
  "arguments": {
    "filters": {
      "limit": 10,
      "state": "sale"
    }
  }
}
```

## 🚨 Troubleshooting

### Error: "Missing Odoo credentials"

**Problema**: El servidor no puede encontrar las credenciales
**Solución**: 
1. Verificar que los headers estén configurados correctamente
2. Revisar los logs del servidor para ver qué headers se están recibiendo
3. Probar con curl primero

### Error: "Authentication failed"

**Problema**: Las credenciales son incorrectas
**Solución**:
1. Verificar que las credenciales funcionen en Odoo directamente
2. Asegurarse de que el usuario tenga permisos de API
3. Verificar la URL y base de datos

### Error: Connection timeout

**Problema**: No puede conectar al servidor Odoo
**Solución**:
1. Verificar que la URL de Odoo sea accesible
2. Revisar firewall y configuraciones de red
3. Probar con timeout más alto

## 📋 Checklist de Configuración

- [ ] Servidor MCP desplegado y funcionando (`/health` responde OK)
- [ ] n8n puede alcanzar el endpoint del servidor MCP
- [ ] Header Auth account creada en n8n con credenciales correctas
- [ ] Credenciales de Odoo verificadas (funcionan en Odoo directamente)
- [ ] Nodo MCP configurado con el Header Auth account
- [ ] Prueba básica funcionando (`tools/list` retorna herramientas)

## 🎯 Configuración Final Recomendada

Basándote en tus capturas de pantalla, esta es la configuración exacta que deberías usar:

### En el Header Auth Account de n8n:
```
Name: odoo_url
Value: https://tu-odoo-real.com

Name: odoo_db
Value: tu_base_datos_real

Name: odoo_username  
Value: tu_usuario_real

Name: odoo_password
Value: tu_password_real
```

### En el nodo MCP:
- **Endpoint**: `https://n8n-odoo.e2zone.easypanel.host/mcp`
- **Server Transport**: `HTTP Streamable`
- **Authentication**: Seleccionar tu Header Auth account
- **Tools to Include**: `All`
- **Timeout**: `60000` (como tienes configurado)

¡Con esta configuración debería funcionar perfectamente! El servidor ya está preparado para recibir las credenciales en el formato que n8n las envía.
