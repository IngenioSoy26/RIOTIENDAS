# Guía de pruebas y demostración

## Cuentas demo

Contraseña para todas: `Rio2026*`

| Experiencia | Cuenta |
|---|---|
| Dueño / administrador | `admin@riotiendas.app` |
| Cajero | `cajero@riotiendas.app` |
| Empleado | `empleado@riotiendas.app` |
| Domiciliario | `domiciliario@riotiendas.app` |
| Cliente | `cliente@riotiendas.app` |

## Demostración recomendada para una feria

### Escena 1 — Cliente

1. Inicia sesión como `cliente@riotiendas.app`.
2. Agrega dos productos.
3. Confirma el pedido a domicilio.
4. Abre “Mis pedidos”: debe aparecer como **Pedido recibido**.

### Escena 2 — Empleado o administrador

1. Inicia sesión como administrador o empleado.
2. Abre Pedidos.
3. Cambia el pedido a **Preparando**.
4. Cambia el pedido a **Listo**.

### Escena 3 — Administrador

1. Asigna el pedido a Miguel Domiciliario.
2. El pedido sigue listo, pero queda asociado al repartidor.

### Escena 4 — Domiciliario

1. Inicia sesión como `domiciliario@riotiendas.app`.
2. Verás únicamente sus pedidos asignados.
3. Pulsa **Iniciar entrega**.
4. Pulsa **Confirmar entregado**.

Cuando se entrega, el backend registra la venta correspondiente sin descontar el inventario dos veces.

### Escena 5 — Caja / POS

1. Entra como cajero.
2. Abre Ventas / Caja.
3. Busca un producto o usa “Escanear código”.
4. Usa uno de los códigos demo, por ejemplo `7701234500011`.
5. Cobra la venta.
6. Revisa Inventario: las existencias se redujeron.

### Escena 6 — Compra de mercancía

1. Entra como empleado.
2. Abre Compras.
3. Registra una reposición.
4. Revisa Inventario: las unidades aumentaron.

### Escena 7 — Control y auditoría

Con el administrador muestra:

- dashboard;
- alertas;
- reportes PDF/Excel/CSV;
- historial de actividad;
- respaldo JSON;
- usuarios y permisos personalizados.

## Pruebas automatizadas

```bash
cd backend
pytest -q
```

La batería cubre:

- cinco roles demo;
- venta y descuento de inventario;
- compra y aumento de inventario;
- pedido del cliente;
- preparación y asignación;
- entrega del domiciliario;
- creación automática de venta al entregar;
- dashboard;
- alertas;
- búsqueda;
- reportes CSV/XLSX/PDF;
- historial;
- respaldo;
- denegación por permisos;
- registro de una tienda nueva;
- recuperación de contraseña en modo demo.
