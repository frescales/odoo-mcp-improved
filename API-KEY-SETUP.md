# 🔐 Configuración con API Key de Odoo

El servidor MCP **YA SOPORTA API KEY** desde la versión actual. No necesitas hacer cambios en el código, solo configurar las variables de entorno correctamente.

## ✅ Cómo funciona actualmente

El código en `src/odoo_mcp/odoo_client.py` **ya tiene soporte para API key**:

```python
# API key takes priority over password
if "ODOO_API_KEY" in os.environ:
    config["api_key"] = os.environ["ODOO_API_KEY"]
elif "ODOO_PASSWORD" in os.environ:
    config["password"] = os.environ["ODOO_PASSWORD"]
```

## 🚀 Configuración en EasyPanel

### Opción 1: Usar API Key (Recomendado)

En EasyPanel, configura estas variables de entorno:

```env
ODOO_URL=https://tu-instancia-odoo.com
ODOO_DB=nombre_de_tu_base_de_datos
ODOO_USERNAME=tu_usuario_odoo
ODOO_API_KEY=tu_api_key_de_odoo
PORT=8000
HOST=0.0.0.0
```

**IMPORTANTE:** 
- Usa `ODOO_API_KEY` en lugar de `ODOO_PASSWORD`
- El API key tiene **prioridad** sobre la contraseña si ambos están presentes
- No necesitas tener `ODOO_PASSWORD` si usas `ODOO_API_KEY`

### Opción 2: Usar Contraseña (Fallback)

Si no tienes API key, puedes seguir usando contraseña:

```env
ODOO_URL=https://tu-instancia-odoo.com
ODOO_DB=nombre_de_tu_base_de_datos
ODOO_USERNAME=tu_usuario_odoo
ODOO_PASSWORD=tu_contraseña_odoo
PORT=8000
HOST=0.0.0.0
```

## 🔑 Cómo obtener tu API Key en Odoo

### Paso 1: Acceder a Odoo
1. Inicia sesión en tu instancia de Odoo
2. Ve a tu perfil (clic en tu nombre arriba a la derecha)

### Paso 2: Habilitar API Key
1. En **Preferencias** → **Account Security**
2. Busca la sección **"API Keys"** o **"External API"**
3. Click en **"New API Key"**
4. Dale un nombre descriptivo (ej: "MCP Server")
5. Copia el API Key generado

### Paso 3: Configurar en EasyPanel
1. Ve a tu servicio en EasyPanel
2. Edita las variables de entorno
3. **Reemplaza** `ODOO_PASSWORD` con `ODOO_API_KEY`
4. Pega tu API Key
5. Reinicia el servicio

## ✅ Verificar que funciona

### 1. Revisa los logs
En los logs de EasyPanel deberías ver:

```
Odoo client configuration:
  URL: https://tu-instancia.com
  Database: tu_db
  Username: tu_usuario
  Authentication: API Key    ← Confirma que dice "API Key"
  Timeout: 30s
  Verify SSL: True
```

### 2. Prueba de salud
```bash
curl https://tu-dominio.easypanel.host/health
```

Debe responder:
```json
{
  "status": "healthy",
  "service": "odoo-mcp-server",
  "version": "1.3.0"
}
```

### 3. Prueba una herramienta
```bash
curl -X POST https://tu-dominio.easypanel.host/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_employee",
      "arguments": {
        "name": "test"
      }
    }
  }'
```

## 🎯 Ventajas de usar API Key

1. **Más seguro**: No expones tu contraseña
2. **Revocable**: Puedes revocar el API key sin cambiar tu contraseña
3. **Auditable**: Odoo registra las conexiones por API key
4. **Específico**: Cada aplicación tiene su propio key

## 🔄 Migrar de contraseña a API Key

Si ya tienes el servidor funcionando con contraseña:

1. **Genera tu API Key** en Odoo (ver pasos arriba)
2. **Edita las variables de entorno** en EasyPanel:
   - Agrega: `ODOO_API_KEY=tu_nuevo_api_key`
   - Opcional: Elimina `ODOO_PASSWORD` (el API key tiene prioridad)
3. **Reinicia el servicio** en EasyPanel
4. **Verifica los logs** para confirmar que usa "API Key"

## 🐛 Solución de problemas

### Error: "Authentication failed: Invalid username or API key"

**Causas comunes:**
- API key incorrecto o expirado
- Usuario no tiene permisos de API
- API key no está habilitado en tu instancia de Odoo

**Solución:**
1. Verifica que el API key esté activo en Odoo
2. Genera un nuevo API key
3. Confirma que el usuario tiene permisos XML-RPC

### El servidor sigue usando contraseña

**Causa:** Ambas variables están presentes pero el código prioriza API key

**Solución:**
1. Verifica que la variable se llame exactamente `ODOO_API_KEY`
2. Reinicia el servicio después de cambiar variables
3. Revisa los logs para ver qué método de autenticación usa

### Error de conexión después del cambio

**Causa:** Configuración incorrecta del API key

**Solución:**
1. Copia el API key completo (sin espacios)
2. Verifica que no haya caracteres especiales mal codificados
3. Prueba primero con contraseña para confirmar que Odoo responde

## 📝 Resumen

**El servidor MCP YA soporta API key**. No necesitas modificar el código, solo:

1. ✅ Genera tu API key en Odoo
2. ✅ Configura `ODOO_API_KEY` en EasyPanel
3. ✅ Reinicia el servicio
4. ✅ Verifica en los logs que usa "API Key"

¡Eso es todo! 🎉
