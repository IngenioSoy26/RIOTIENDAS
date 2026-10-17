from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.esquemas.comunes import CompraCrear
from app.modelos.modelos import Compra, DetalleCompra, Usuario
from app.servicios.servicio_inventario import ServicioInventario
from app.servicios.utilidades import numero_documento, registrar_actividad


class ServicioCompras:
    def __init__(self, db: Session, usuario: Usuario):
        self.db = db
        self.usuario = usuario
        self.inventario = ServicioInventario(db, usuario)

    def crear_compra(self, datos: CompraCrear):
        if not datos.lineas:
            raise HTTPException(status_code=400, detail="La compra debe incluir productos.")

        numero = numero_documento("COM")
        total = sum(linea.cantidad * linea.costo_unitario for linea in datos.lineas)
        compra = Compra(
            tienda_id=self.usuario.tienda_id,
            proveedor_id=datos.proveedor_id,
            usuario_id=self.usuario.id,
            numero=numero,
            total=round(total, 2),
            observacion=datos.observacion,
        )
        self.db.add(compra)
        self.db.flush()

        for linea in datos.lineas:
            producto = self.inventario.obtener_producto(linea.producto_id)
            producto.precio_compra = linea.costo_unitario
            self.db.add(DetalleCompra(
                compra_id=compra.id,
                producto_id=producto.id,
                cantidad=linea.cantidad,
                costo_unitario=linea.costo_unitario,
                subtotal=round(linea.cantidad * linea.costo_unitario, 2),
            ))
            self.inventario.cambiar_existencia(producto, linea.cantidad, "compra", numero)

        registrar_actividad(
            self.db, self.usuario.tienda_id, self.usuario.id,
            "compra_registrada", "compra", compra.id,
            f"Compra {numero} por ${total:,.0f}.",
        )
        self.db.commit()
        self.db.refresh(compra)
        return compra
