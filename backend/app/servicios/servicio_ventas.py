from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.esquemas.comunes import VentaCrear
from app.modelos.modelos import DetalleVenta, Usuario, Venta
from app.servicios.servicio_inventario import ServicioInventario
from app.servicios.utilidades import numero_documento, registrar_actividad


class ServicioVentas:
    def __init__(self, db: Session, usuario: Usuario):
        self.db = db
        self.usuario = usuario
        self.inventario = ServicioInventario(db, usuario)

    def crear_venta(self, datos: VentaCrear):
        if not datos.lineas:
            raise HTTPException(status_code=400, detail="La venta debe tener al menos un producto.")

        subtotal = 0.0
        costo_total = 0.0
        lineas_preparadas = []

        # Validamos todo antes de descontar stock. Así una venta no queda a medias.
        for linea in datos.lineas:
            producto = self.inventario.obtener_producto(linea.producto_id)
            if producto.cantidad_disponible < linea.cantidad:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para {producto.nombre}.")
            valor_linea = producto.precio_venta * linea.cantidad
            costo_linea = producto.precio_compra * linea.cantidad
            subtotal += valor_linea
            costo_total += costo_linea
            lineas_preparadas.append((producto, linea.cantidad, valor_linea))

        descuento = min(datos.descuento, subtotal)
        total = round(subtotal - descuento, 2)
        numero = numero_documento("VTA")

        venta = Venta(
            tienda_id=self.usuario.tienda_id,
            usuario_id=self.usuario.id,
            cliente_id=datos.cliente_id,
            numero=numero,
            subtotal=round(subtotal, 2),
            descuento=round(descuento, 2),
            impuesto=0,
            total=total,
            costo_total=round(costo_total, 2),
            ganancia_estimada=round(total - costo_total, 2),
            metodo_pago=datos.metodo_pago,
        )
        self.db.add(venta)
        self.db.flush()

        for producto, cantidad, valor_linea in lineas_preparadas:
            self.db.add(DetalleVenta(
                venta_id=venta.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=producto.precio_venta,
                costo_unitario=producto.precio_compra,
                subtotal=round(valor_linea, 2),
            ))
            self.inventario.cambiar_existencia(producto, -cantidad, "venta", numero)

        registrar_actividad(
            self.db, self.usuario.tienda_id, self.usuario.id,
            "venta_creada", "venta", venta.id,
            f"Venta {numero} por ${total:,.0f}.",
        )
        self.db.commit()
        self.db.refresh(venta)
        return venta
