# Arquitectura de RIOTIENDAS

## 1. Objetivo técnico

El MVP fue diseñado para demostrar el comportamiento completo de una tienda de barrio sin depender de servicios pagos. La prioridad es que un aprendiz pueda abrir el proyecto, entenderlo, modificarlo y ejecutarlo.

## 2. Arquitectura

```text
┌────────────────────────────────────────────────────────────┐
│                 PWA / navegador / app móvil                │
│              HTML + CSS + JavaScript modular               │
└──────────────────────────┬─────────────────────────────────┘
                           │ REST + JWT
┌──────────────────────────▼─────────────────────────────────┐
│                        FastAPI                             │
│ Autenticación │ Roles │ Inventario │ Ventas │ Pedidos ... │
└──────────────────────────┬─────────────────────────────────┘
                           │ SQLAlchemy
┌──────────────────────────▼─────────────────────────────────┐
│ SQLite (desarrollo) / PostgreSQL (producción)              │
└────────────────────────────────────────────────────────────┘
```

## 3. Razones para esta decisión

- Un solo backend en Python.
- Frontend sin compilación: más sencillo para fines educativos.
- La interfaz se sirve desde el mismo FastAPI, reduciendo problemas de CORS en el MVP.
- PWA instalable desde Android/desktop.
- API reutilizable si luego se crea una aplicación nativa.
- SQLAlchemy permite migrar a PostgreSQL sin reescribir la lógica de negocio.

## 4. Separación de responsabilidades

### `core`
Configuración, JWT, hash de contraseñas y permisos.

### `database`
Motor y sesiones SQLAlchemy.

### `modelos`
Estructura relacional de la base de datos.

### `esquemas`
Validación de entradas con Pydantic.

### `servicios`
Reglas de negocio. Ejemplo: una venta valida el stock antes de descontarlo.

### `api`
Endpoints HTTP. Deben ser delgados: reciben datos, verifican acceso y delegan en servicios.

### `seed`
Datos demostrativos.

### `static`
Aplicación cliente/PWA.

## 5. Roles y flujo real

### Administrador
Control total, usuarios, permisos, reportes, historial, compras, ventas y pedidos.

### Cajero
Venta POS, inventario de consulta, clientes, pedidos y reportes permitidos.

### Empleado
Inventario, ajustes, compras, proveedores, preparación de pedidos y alertas.

### Domiciliario
Solo ve pedidos que le fueron asignados y puede cambiar `listo → en_camino → entregado`.

### Cliente
Ve catálogo, crea pedidos y consulta su propio seguimiento.

## 6. Flujo del inventario

```text
Compra         + existencia
Ajuste         +/- existencia
Venta POS      - existencia
Pedido creado  - existencia (reserva)
Pedido cancel. + existencia
Pedido entrega no vuelve a descontar
```

La reserva de un pedido se hace desde la creación. Así no se vende por caja una unidad ya comprometida para domicilio.

## 7. Offline

El shell de la PWA se guarda en caché. Los pedidos pueden quedar en una cola local y sincronizarse al recuperar conexión.

**Decisión deliberada:** una venta POS no se confirma offline. Permitirlo sin un protocolo de reconciliación puede producir sobreventa cuando existen varias cajas. Para un sistema comercial real, el siguiente nivel sería agregar idempotencia, versión de inventario y resolución explícita de conflictos.
