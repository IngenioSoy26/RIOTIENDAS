from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.seguridad import crear_hash_contrasena
from app.modelos.modelos import Categoria, Cliente, Producto, Proveedor, Tienda, Usuario


PRODUCTOS = [
    ("Gaseosa Cola 1.5 L", "7701234500011", "BEB-001", "Gaseosa", 4200, 6500, 32, 8, "unidad"),
    ("Arroz 1 kg", "7701234500028", "ABR-001", "CampoFino", 3100, 4500, 24, 6, "unidad"),
    ("Leche entera 1 L", "7701234500035", "LAC-001", "La Vaquita", 2900, 4200, 14, 5, "unidad"),
    ("Huevos x12", "7701234500042", "HUE-012", "Granja", 6800, 9000, 10, 4, "cubeta"),
    ("Pan tajado", "7701234500059", "PAN-001", "Pan Rico", 4800, 6800, 4, 5, "unidad"),
    ("Aceite vegetal 1 L", "7701234500066", "ACE-001", "Sol", 7200, 9800, 12, 4, "unidad"),
    ("Galletas surtidas", "7701234500073", "GAL-001", "Dulce", 1500, 2500, 40, 10, "unidad"),
    ("Atún en lata", "7701234500080", "LAT-001", "Mar Azul", 4300, 6200, 18, 5, "unidad"),
    ("Papel higiénico x4", "7701234500097", "ASE-001", "Suave", 6200, 8500, 15, 5, "paquete"),
    ("Detergente 500 g", "7701234500103", "ASE-002", "Limpio", 3600, 5400, 20, 6, "unidad"),
    ("Agua 600 ml", "7701234500110", "BEB-002", "Sierra", 900, 1800, 50, 12, "unidad"),
    ("Café 250 g", "7701234500127", "CAF-001", "Montaña", 6500, 9200, 16, 4, "unidad"),
]


def cargar_datos_iniciales(db: Session):
    """Carga una tienda demostrativa únicamente cuando la base está vacía."""
    if db.query(Tienda).first():
        return

    tienda = Tienda(
        nombre="RioTiendas Demo - Tienda La Esquina",
        nit="900.000.001-0",
        telefono="3000000000",
        direccion="Riohacha, La Guajira",
        correo="demo@riotiendas.app",
    )
    db.add(tienda)
    db.flush()

    categorias = {}
    for nombre in ["Bebidas", "Abarrotes", "Lácteos", "Huevos y pan", "Aseo", "Snacks", "Enlatados"]:
        categoria = Categoria(tienda_id=tienda.id, nombre=nombre)
        db.add(categoria)
        db.flush()
        categorias[nombre] = categoria

    proveedor = Proveedor(
        tienda_id=tienda.id,
        nombre="Distribuciones Guajira SAS",
        telefono="3001112233",
        direccion="Zona comercial de Riohacha",
        correo="ventas@distribuciones.demo",
        notas="Proveedor demostrativo.",
    )
    db.add(proveedor)
    db.flush()

    cliente = Cliente(
        tienda_id=tienda.id,
        nombre="María Cliente Demo",
        telefono="3005556677",
        direccion="Calle 10 # 5-20, Riohacha",
        correo="cliente@riotiendas.app",
    )
    db.add(cliente)
    db.flush()

    contrasena = crear_hash_contrasena("Rio2026*")
    usuarios = [
        Usuario(tienda_id=tienda.id, nombre="Ana Administradora", correo="admin@riotiendas.app", telefono="3001000001", contrasena_hash=contrasena, rol="administrador"),
        Usuario(tienda_id=tienda.id, nombre="Carlos Cajero", correo="cajero@riotiendas.app", telefono="3001000002", contrasena_hash=contrasena, rol="cajero"),
        Usuario(tienda_id=tienda.id, nombre="Laura Empleada", correo="empleado@riotiendas.app", telefono="3001000003", contrasena_hash=contrasena, rol="empleado"),
        Usuario(tienda_id=tienda.id, nombre="Miguel Domiciliario", correo="domiciliario@riotiendas.app", telefono="3001000004", contrasena_hash=contrasena, rol="domiciliario"),
        Usuario(tienda_id=tienda.id, cliente_id=cliente.id, nombre="María Cliente Demo", correo="cliente@riotiendas.app", telefono="3005556677", contrasena_hash=contrasena, rol="cliente"),
    ]
    db.add_all(usuarios)

    mapa_categoria = {
        "Gaseosa": "Bebidas", "CampoFino": "Abarrotes", "La Vaquita": "Lácteos",
        "Granja": "Huevos y pan", "Pan Rico": "Huevos y pan", "Sol": "Abarrotes",
        "Dulce": "Snacks", "Mar Azul": "Enlatados", "Suave": "Aseo", "Limpio": "Aseo",
        "Sierra": "Bebidas", "Montaña": "Abarrotes",
    }

    for nombre, barras, interno, marca, compra, venta, cantidad, minimo, unidad in PRODUCTOS:
        vencimiento = date.today() + timedelta(days=20) if nombre == "Leche entera 1 L" else None
        db.add(Producto(
            tienda_id=tienda.id,
            categoria_id=categorias[mapa_categoria[marca]].id,
            proveedor_id=proveedor.id,
            nombre=nombre,
            codigo_barras=barras,
            codigo_interno=interno,
            marca=marca,
            precio_compra=compra,
            precio_venta=venta,
            cantidad_disponible=cantidad,
            stock_minimo=minimo,
            unidad_medida=unidad,
            fecha_vencimiento=vencimiento,
        ))

    db.commit()
