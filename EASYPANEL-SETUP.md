# 🚀 Guía de Despliegue en EasyPanel

Esta guía te llevará paso a paso para desplegar tu servidor MCP de Odoo en EasyPanel y conectarlo con n8n.

## ✅ Prerrequisitos

- [ ] Cuenta en EasyPanel (Hostinger VPS)
- [ ] Instancia de Odoo funcionando
- [ ] Credenciales de Odoo (URL, base de datos, usuario, contraseña)
- [ ] n8n configurado

## 📋 Paso 1: Configurar en EasyPanel

### 1.1 Crear nuevo servicio

1. **Accede a tu panel de EasyPanel**
2. **Click en "Create"** → **"Service"**
3. **Selecciona "GitHub"** como fuente

### 1.2 Configurar repositorio

```
Repository: frescales/odoo-mcp-improved
Branch: http-server
Build Method: Dockerfile
Dockerfile Path: Dockerfile.http
```

### 1.3 Variables de entorno

En la sección **Environment**, agrega estas variables:

```env
ODOO_URL=https://tu-instancia-odoo.com
ODOO_DB=nombre_de_tu_base_de_datos
ODOO_USERNAME=tu_usuario_odoo
ODOO_PASSWORD=tu_contraseña_odoo
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
```

### 1.4 Configuración del puerto

- **Port**: `8000`
- **Protocol**: `HTTP`
- **Domain**: Asigna un dominio o usa el generado automáticamente

### 1.5 Desplegar

1. **Click en "Deploy"**
2. **Espera a que termine el build** (2-3 minutos)
3. **Verifica el estado** en los logs

## 🔍 Paso 2: Verificar el despliegue

### 2.1 Prueba de salud

Visita: `https://tu-dominio.easypanel.host/health`

Deberías ver:
```json
{
  "status": "healthy",
  "service": "odoo-mcp-server",
  "version": "1.1.0"
}
```

### 2.2 Información del servidor

Visita: `https://tu-dominio.easypanel.host/`

Deberías ver la información completa del servidor y endpoints disponibles.

### 2.3 Prueba básica de MCP

```bash
curl -X POST https://tu-dominio.easypanel.host/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

## 🔗 Paso 3: Configurar n8n

### 3.1 Instalar MCP Client Tool

1. En n8n, busca **"MCP Client"** en los nodos
2. Si no está disponible, instálalo desde la comunidad

### 3.2 Configurar conexión MCP

En tu flujo de n8n, agrega un nodo **MCP Client** con esta configuración:

```
Connection Type: HTTP
URL: https://tu-dominio.easypanel.host/mcp
Method: POST
Headers: 
  Content-Type: application/json
```

### 3.3 Probar herramientas

Usa estas herramientas de Odoo disponibles:

**Ventas:**
- `search_sales_orders` - Buscar órdenes de venta
- `create_sales_order` - Crear nueva orden de venta
- `analyze_sales_performance` - Analizar rendimiento de ventas

**Compras:**
- `search_purchase_orders` - Buscar órdenes de compra
- `create_purchase_order` - Crear orden de compra
- `analyze_supplier_performance` - Analizar proveedores

**Inventario:**
- `check_product_availability` - Verificar stock
- `create_inventory_adjustment` - Ajustar inventario
- `analyze_inventory_turnover` - Rotación de inventario

**Contabilidad:**
- `search_journal_entries` - Buscar asientos contables
- `create_journal_entry` - Crear asiento contable
- `analyze_financial_ratios` - Ratios financieros

**RRHH:**
- `search_employee` - Buscar empleados
- `search_holidays` - Buscar vacaciones

## 🐛 Solución de problemas

### Error: "Connection refused"

✅ **Verificar variables de entorno:**
```bash
# En EasyPanel logs, verifica que aparezcan:
Environment check:
  ODOO_URL: https://tu-odoo.com
  ODOO_DB: tu_db
  ODOO_USERNAME: tu_user
```

### Error: "Tool not found"

✅ **Listar herramientas disponibles:**
```bash
curl -X POST https://tu-dominio.easypanel.host/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### Error de conexión a Odoo

✅ **Verificar credenciales:**
1. Prueba las credenciales directamente en Odoo
2. Verifica que la API XML-RPC esté habilitada
3. Confirma que no hay restricciones de IP

### Error 503 en health check

✅ **Revisar logs del contenedor:**
1. Ve a EasyPanel → Tu servicio → Logs
2. Busca errores de inicialización
3. Verifica que todas las dependencias se instalaron

## 📚 Ejemplos de uso en n8n

### Ejemplo 1: Buscar cliente por nombre

```json
{
  "method": "tools/call",
  "params": {
    "name": "search_employee",
    "arguments": {
      "name": "Juan Perez"
    }
  }
}
```

### Ejemplo 2: Verificar stock de producto

```json
{
  "method": "tools/call",
  "params": {
    "name": "check_product_availability",
    "arguments": {
      "params": {
        "product_ids": [123, 456]
      }
    }
  }
}
```

### Ejemplo 3: Crear orden de venta

```json
{
  "method": "tools/call",
  "params": {
    "name": "create_sales_order",
    "arguments": {
      "order": {
        "partner_id": 123,
        "order_lines": [
          {
            "product_id": 456,
            "product_uom_qty": 2
          }
        ]
      }
    }
  }
}
```

## 🎯 Siguientes pasos

1. **Configurar autenticación** (si es necesario)
2. **Implementar rate limiting** para producción
3. **Configurar monitoring** y alertas
4. **Crear backups** de la configuración
5. **Documentar flujos de n8n** específicos

## 🆘 Soporte

Si tienes problemas:

1. **Revisa los logs** en EasyPanel
2. **Verifica la conectividad** a Odoo
3. **Prueba los endpoints** manualmente
4. **Consulta la documentación** completa en [README-HTTP.md](README-HTTP.md)

¡Tu servidor MCP de Odoo ya está listo para usar con n8n! 🎉
