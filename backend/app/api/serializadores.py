from sqlalchemy.orm import Session

from app.modelos.modelos import DetallePedido, Pedido, Producto, Usuario


def producto_diccionario(producto: Producto) -> dict:
    ganancia = producto.precio_venta - producto.precio_compra
    if producto.cantidad_disponible <= 0:
        estado = "agotado"
    elif producto.cantidad_disponible <= producto.stock_minimo:
        estado = "poco_inventario"
    else:
        estado = "disponible"

    return {
        "id": producto.id,
        "nombre": producto.nombre,
        "codigo_barras": producto.codigo_barras,
        "codigo_interno": producto.codigo_interno,
        "categoria_id": producto.categoria_id,
        "proveedor_id": producto.proveedor_id,
        "marca": producto.marca,
        "precio_compra": producto.precio_compra,
        "precio_venta": producto.precio_venta,
        "ganancia_unitaria": round(ganancia, 2),
        "cantidad_disponible": producto.cantidad_disponible,
        "stock_minimo": producto.stock_minimo,
        "unidad_medida": producto.unidad_medida,
        "fecha_vencimiento": producto.fecha_vencimiento.isoformat() if producto.fecha_vencimiento else None,
        "imagen_url": producto.imagen_url,
        "activo": producto.activo,
        "estado": estado,
    }


def pedido_diccionario(db: Session, pedido: Pedido) -> dict:
    detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido.id).all()
    lineas = []
    for detalle in detalles:
        producto = db.get(Producto, detalle.producto_id)
        lineas.append({
            "producto_id": detalle.producto_id,
            "producto": producto.nombre if producto else f"Producto {detalle.producto_id}",
            "cantidad": detalle.cantidad,
            "precio_unitario": detalle.precio_unitario,
            "subtotal": detalle.subtotal,
        })

    domiciliario = db.get(Usuario, pedido.domiciliario_id) if pedido.domiciliario_id else None
    return {
        "id": pedido.id,
        "numero": pedido.numero,
        "nombre_cliente": pedido.nombre_cliente,
        "telefono": pedido.telefono,
        "direccion": pedido.direccion,
        "notas": pedido.notas,
        "subtotal": pedido.subtotal,
        "costo_domicilio": pedido.costo_domicilio,
        "total": pedido.total,
        "metodo_pago": pedido.metodo_pago,
        "estado": pedido.estado,
        "domiciliario_id": pedido.domiciliario_id,
        "domiciliario_nombre": domiciliario.nombre if domiciliario else None,
        "fecha": pedido.fecha.isoformat(),
        "lineas": lineas,
    }
