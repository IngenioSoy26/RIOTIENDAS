# RIOTIENDAS — MVP funcional

**Lema:** *Tu tienda en orden, tu negocio en crecimiento.*

RIOTIENDAS es una aplicación web instalable tipo **PWA** orientada a tiendas, minimercados y negocios de barrio. Esta versión integra backend, base de datos, interfaz, roles, inventario, caja POS, compras, proveedores, clientes, pedidos a domicilio, domiciliarios, reportes, alertas, historial y copias de seguridad.

## Arquitectura elegida

Se usa **FastAPI + SQLAlchemy + SQLite + PWA en HTML/CSS/JavaScript**.

Se eligió esta arquitectura porque permite entregar una demo funcional sin proceso de compilación del frontend, mantener Python como núcleo, instalar la app desde el navegador y reutilizar la misma API más adelante desde Android/iOS.

## Módulos incluidos

- Autenticación con JWT.
- Roles: administrador, cajero, empleado, domiciliario y cliente.
- Permisos por rol y permisos personalizados.
- Productos, categorías e inventario.
- Búsqueda y lectura de código de barras.
- POS / caja.
- Clientes.
- Proveedores y compras.
- Pedidos a domicilio.
- Asignación de domiciliarios y estados del pedido.
- Dashboard con indicadores y gráficas.
- Alertas de inventario y vencimiento.
- Reportes CSV, XLSX y PDF.
- Historial de actividades.
- Búsqueda global.
- Copia de seguridad JSON.
- PWA con caché del shell y cola básica de pedidos sin conexión. Las ventas POS requieren conexión para preservar la integridad del inventario.

## Usuarios de demostración

Todos usan la contraseña `Rio2026*`.

| Rol | Correo |
|---|---|
| Administrador | `admin@riotiendas.app` |
| Cajero | `cajero@riotiendas.app` |
| Empleado | `empleado@riotiendas.app` |
| Domiciliario | `domiciliario@riotiendas.app` |
| Cliente | `cliente@riotiendas.app` |

## Paleta derivada del logo

- Azul profundo: `#073565`
- Azul medio: `#0A4E91`
- Naranja principal: `#F36A08`
- Naranja brillante: `#FF8A00`
- Amarillo acento: `#FFB21A`
- Fondo claro: `#F6F8FB`
- Texto: `#172033`
- Éxito: `#16A567`
- Peligro: `#D92D20`

## Ejecutar en Windows

```powershell
cd backend
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\python.exe -m uvicorn app.main:aplicacion --reload --host 127.0.0.1 --port 8000
```

Se invoca `python.exe` del entorno virtual directamente para evitar depender de la
activación con `Activate.ps1`, que puede fallar según la política de ejecución de
scripts de Windows. Si tu sistema tiene `python` en el PATH, también sirve
`python -m venv .venv` y luego `.venv\Scripts\Activate.ps1`.

Para probar la app desde un celular en la misma red Wi-Fi, inicia el servidor con
`--host 0.0.0.0 --port 8000` y abre `http://IP-DE-TU-PC:8000`.

Luego abre:

```text
http://127.0.0.1:8000
```

Documentación de la API:

```text
http://127.0.0.1:8000/docs
```

## Pruebas

```powershell
cd backend
pytest -q
```

## Importante sobre el modo sin conexión

La PWA puede abrir la interfaz en caché y encolar ciertas operaciones si se pierde Internet. Para un uso comercial real con múltiples cajas, la sincronización offline necesita una capa adicional de resolución de conflictos para impedir ventas sobre inventario desactualizado.

Consulta `docs/ARQUITECTURA.md`, `docs/PRUEBAS_Y_DEMOS.md` y `docs/DESPLIEGUE.md`.


## Empaquetado Android/iOS

La carpeta `mobile/` contiene una configuración inicial de Capacitor. La PWA puede instalarse directamente desde el navegador y, cuando exista un dominio HTTPS estable, puede envolverse como aplicación Android/iOS.

## Validación realizada

El backend fue ejecutado localmente y la batería automatizada completa finalizó correctamente con **6 pruebas aprobadas**. Los módulos JavaScript también fueron validados sintácticamente con Node.js.
