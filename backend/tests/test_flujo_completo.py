import os
from pathlib import Path

# La variable se define antes de importar la aplicación para que SQLAlchemy
# construya el motor apuntando a una base exclusiva para las pruebas.
BASE_PRUEBAS = Path(__file__).resolve().parent / "riotiendas_pruebas.db"
if BASE_PRUEBAS.exists():
    BASE_PRUEBAS.unlink()
os.environ["APP_URL_BD"] = f"sqlite:///{BASE_PRUEBAS}"
os.environ["APP_AMBIENTE"] = "pruebas"

from fastapi.testclient import TestClient

from app.main import aplicacion


CLAVE = "Rio2026*"


def iniciar(cliente: TestClient, correo: str) -> str:
    respuesta = cliente.post(
        "/api/autenticacion/ingresar",
        json={"correo": correo, "contrasena": CLAVE},
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


def cabecera(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_salud_interfaz_y_roles_demo():
    with TestClient(aplicacion) as cliente:
        assert cliente.get("/api/salud").status_code == 200
        assert cliente.get("/").status_code == 200
        assert "RioTiendas" in cliente.get("/").text

        for correo, rol in [
            ("admin@riotiendas.app", "administrador"),
            ("cajero@riotiendas.app", "cajero"),
            ("empleado@riotiendas.app", "empleado"),
            ("domiciliario@riotiendas.app", "domiciliario"),
            ("cliente@riotiendas.app", "cliente"),
        ]:
            token = iniciar(cliente, correo)
            perfil = cliente.get("/api/autenticacion/yo", headers=cabecera(token))
            assert perfil.status_code == 200
            assert perfil.json()["rol"] == rol


def test_flujo_venta_compra_e_inventario():
    with TestClient(aplicacion) as cliente:
        token_cajero = iniciar(cliente, "cajero@riotiendas.app")
        productos = cliente.get("/api/productos", headers=cabecera(token_cajero)).json()
        producto = productos[0]
        stock_inicial = producto["cantidad_disponible"]

        venta = cliente.post(
            "/api/ventas",
            headers=cabecera(token_cajero),
            json={
                "lineas": [{"producto_id": producto["id"], "cantidad": 2}],
                "descuento": 500,
                "metodo_pago": "efectivo",
            },
        )
        assert venta.status_code == 200, venta.text
        assert venta.json()["total"] > 0

        actualizado = cliente.get(
            f"/api/productos/codigo/{producto['codigo_barras']}",
            headers=cabecera(token_cajero),
        ).json()
        assert actualizado["cantidad_disponible"] == stock_inicial - 2

        token_empleado = iniciar(cliente, "empleado@riotiendas.app")
        proveedores = cliente.get("/api/proveedores", headers=cabecera(token_empleado)).json()
        compra = cliente.post(
            "/api/compras",
            headers=cabecera(token_empleado),
            json={
                "proveedor_id": proveedores[0]["id"],
                "lineas": [{
                    "producto_id": producto["id"],
                    "cantidad": 5,
                    "costo_unitario": producto["precio_compra"],
                }],
                "observacion": "Reposición automática de prueba",
            },
        )
        assert compra.status_code == 200, compra.text

        producto_post_compra = cliente.get(
            f"/api/productos/codigo/{producto['codigo_barras']}",
            headers=cabecera(token_empleado),
        ).json()
        assert producto_post_compra["cantidad_disponible"] == stock_inicial + 3


def test_flujo_cliente_tienda_pedido_domiciliario_entrega():
    with TestClient(aplicacion) as cliente:
        token_cliente = iniciar(cliente, "cliente@riotiendas.app")
        productos = cliente.get("/api/productos", headers=cabecera(token_cliente)).json()
        producto = next(p for p in productos if p["cantidad_disponible"] >= 3)
        stock_antes = producto["cantidad_disponible"]

        pedido = cliente.post(
            "/api/pedidos",
            headers=cabecera(token_cliente),
            json={
                "metodo_pago": "efectivo",
                "costo_domicilio": 5000,
                "notas": "Prueba cliente → tienda → domiciliario",
                "lineas": [{"producto_id": producto["id"], "cantidad": 2}],
            },
        )
        assert pedido.status_code == 200, pedido.text
        pedido_datos = pedido.json()
        assert pedido_datos["estado"] == "recibido"

        # El stock queda reservado desde que el cliente confirma el pedido.
        productos_despues = cliente.get("/api/productos", headers=cabecera(token_cliente)).json()
        mismo_producto = next(p for p in productos_despues if p["id"] == producto["id"])
        assert mismo_producto["cantidad_disponible"] == stock_antes - 2

        token_admin = iniciar(cliente, "admin@riotiendas.app")
        pedidos_admin = cliente.get("/api/pedidos", headers=cabecera(token_admin)).json()
        pedido_admin = next(p for p in pedidos_admin if p["id"] == pedido_datos["id"])
        assert pedido_admin["nombre_cliente"] == "María Cliente Demo"

        for estado in ["preparando", "listo"]:
            respuesta = cliente.post(
                f"/api/pedidos/{pedido_datos['id']}/estado",
                headers=cabecera(token_admin),
                json={"estado": estado},
            )
            assert respuesta.status_code == 200, respuesta.text

        domiciliarios = cliente.get("/api/domiciliarios", headers=cabecera(token_admin)).json()
        domiciliario_id = domiciliarios[0]["id"]
        asignacion = cliente.post(
            f"/api/pedidos/{pedido_datos['id']}/asignar",
            headers=cabecera(token_admin),
            json={"domiciliario_id": domiciliario_id},
        )
        assert asignacion.status_code == 200, asignacion.text
        assert asignacion.json()["domiciliario_id"] == domiciliario_id

        token_domiciliario = iniciar(cliente, "domiciliario@riotiendas.app")
        propios = cliente.get("/api/pedidos", headers=cabecera(token_domiciliario)).json()
        assert any(p["id"] == pedido_datos["id"] for p in propios)

        for estado in ["en_camino", "entregado"]:
            respuesta = cliente.post(
                f"/api/pedidos/{pedido_datos['id']}/estado",
                headers=cabecera(token_domiciliario),
                json={"estado": estado},
            )
            assert respuesta.status_code == 200, respuesta.text

        ventas = cliente.get("/api/ventas", headers=cabecera(token_admin)).json()
        assert any(v["pedido_id"] == pedido_datos["id"] for v in ventas)


def test_alertas_dashboard_reportes_busqueda_historial_y_respaldo():
    with TestClient(aplicacion) as cliente:
        token_admin = iniciar(cliente, "admin@riotiendas.app")
        headers = cabecera(token_admin)

        dashboard = cliente.get("/api/dashboard", headers=headers)
        assert dashboard.status_code == 200
        assert "ventas_hoy" in dashboard.json()

        alertas = cliente.get("/api/alertas", headers=headers)
        assert alertas.status_code == 200
        assert any(a["tipo"] in {"stock_bajo", "vencimiento", "agotado"} for a in alertas.json())

        busqueda = cliente.get("/api/buscar?q=Pan", headers=headers)
        assert busqueda.status_code == 200
        assert len(busqueda.json()) >= 1

        historial = cliente.get("/api/historial", headers=headers)
        assert historial.status_code == 200
        assert len(historial.json()) >= 1

        for formato, esperado in [
            ("csv", "text/csv"),
            ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("pdf", "application/pdf"),
        ]:
            respuesta = cliente.get(f"/api/reportes/exportar/{formato}", headers=headers)
            assert respuesta.status_code == 200
            assert esperado in respuesta.headers["content-type"]
            assert len(respuesta.content) > 20

        respaldo = cliente.get("/api/respaldo", headers=headers)
        assert respaldo.status_code == 200
        assert "productos" in respaldo.json()


def test_permisos_impiden_acciones_no_autorizadas():
    with TestClient(aplicacion) as cliente:
        token_domiciliario = iniciar(cliente, "domiciliario@riotiendas.app")
        respuesta = cliente.get("/api/reportes/resumen", headers=cabecera(token_domiciliario))
        assert respuesta.status_code == 403

        token_cliente = iniciar(cliente, "cliente@riotiendas.app")
        respuesta = cliente.post(
            "/api/ventas",
            headers=cabecera(token_cliente),
            json={"lineas": [{"producto_id": 1, "cantidad": 1}], "metodo_pago": "efectivo"},
        )
        assert respuesta.status_code == 403


def test_registro_nueva_tienda_y_recuperacion_contrasena_demo():
    with TestClient(aplicacion) as cliente:
        correo = "nueva.tienda@riotiendas.app"
        registro = cliente.post(
            "/api/autenticacion/registrar-tienda",
            json={
                "nombre_tienda": "Tienda Nueva Demo",
                "nombre_administrador": "Nuevo Dueño",
                "correo": correo,
                "telefono": "3009998877",
                "direccion": "Riohacha",
                "contrasena": "ClaveInicial2026*",
            },
        )
        assert registro.status_code == 200, registro.text

        solicitud = cliente.post(
            "/api/autenticacion/solicitar-recuperacion",
            json={"correo": correo},
        )
        assert solicitud.status_code == 200
        token_demo = solicitud.json().get("token_demo")
        assert token_demo

        cambio = cliente.post(
            "/api/autenticacion/restablecer-contrasena",
            json={"token": token_demo, "nueva_contrasena": "NuevaClave2026*"},
        )
        assert cambio.status_code == 200

        ingreso = cliente.post(
            "/api/autenticacion/ingresar",
            json={"correo": correo, "contrasena": "NuevaClave2026*"},
        )
        assert ingreso.status_code == 200


def test_tienda_nueva_crea_cliente_y_compra_desde_la_tienda():
    """Una tienda creada desde cero debe poder operar el flujo de cliente.

    Al registrar la tienda no se precarga ningún dato: el administrador crea la
    categoría, el producto y los usuarios. El usuario con rol cliente debe quedar
    enlazado a un registro de cliente para poder pedir a domicilio y ver sus
    propios pedidos.
    """
    with TestClient(aplicacion) as cliente:
        registro = cliente.post(
            "/api/autenticacion/registrar-tienda",
            json={
                "nombre_tienda": "Tienda Desde Cero",
                "nombre_administrador": "Dueño Desde Cero",
                "correo": "dueno.desdecero@riotiendas.app",
                "telefono": "3001110000",
                "direccion": "Riohacha",
                "contrasena": "ClaveInicial2026*",
            },
        )
        assert registro.status_code == 200, registro.text
        token_admin = registro.json()["access_token"]

        categoria = cliente.post(
            "/api/categorias",
            headers=cabecera(token_admin),
            json={"nombre": "Aseo", "descripcion": ""},
        )
        assert categoria.status_code == 200, categoria.text

        producto = cliente.post(
            "/api/productos",
            headers=cabecera(token_admin),
            json={
                "nombre": "Jabón Desde Cero",
                "codigo_barras": "7709001",
                "categoria_id": categoria.json()["id"],
                "precio_compra": 2000,
                "precio_venta": 3500,
                "cantidad_disponible": 10,
                "stock_minimo": 2,
            },
        )
        assert producto.status_code == 200, producto.text
        producto_id = producto.json()["id"]

        creado = cliente.post(
            "/api/usuarios",
            headers=cabecera(token_admin),
            json={
                "nombre": "Cliente Desde Cero",
                "correo": "cliente.desdecero@riotiendas.app",
                "telefono": "3005550000",
                "direccion": "Calle 1 #2-3",
                "contrasena": "ClaveCliente2026*",
                "rol": "cliente",
            },
        )
        assert creado.status_code == 200, creado.text

        ingreso = cliente.post(
            "/api/autenticacion/ingresar",
            json={"correo": "cliente.desdecero@riotiendas.app", "contrasena": "ClaveCliente2026*"},
        )
        assert ingreso.status_code == 200, ingreso.text
        token_cliente = ingreso.json()["access_token"]

        perfil = cliente.get("/api/autenticacion/yo", headers=cabecera(token_cliente)).json()
        assert perfil["cliente_id"] is not None
        assert perfil["cliente"]["direccion"] == "Calle 1 #2-3"

        pedido = cliente.post(
            "/api/pedidos",
            headers=cabecera(token_cliente),
            json={
                "costo_domicilio": 4000,
                "metodo_pago": "efectivo",
                "notas": "",
                "lineas": [{"producto_id": producto_id, "cantidad": 2}],
            },
        )
        assert pedido.status_code == 200, pedido.text
        assert pedido.json()["direccion"] == "Calle 1 #2-3"
        assert pedido.json()["estado"] == "recibido"

        listado = cliente.get("/api/pedidos", headers=cabecera(token_cliente))
        assert listado.status_code == 200
        assert len(listado.json()) == 1
