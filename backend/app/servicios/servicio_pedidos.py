from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.esquemas.comunes import PedidoCrear
from app.modelos.modelos import Cliente, DetallePedido, DetalleVenta, Pedido, Usuario, Venta
from app.servicios.servicio_inventario import ServicioInventario
from app.servicios.utilidades import numero_documento, registrar_actividad


TRANSICIONES = {
    "recibido": {"preparando", "cancelado"},
    "preparando": {"listo", "cancelado"},
    "listo": {"en_camino", "cancelado"},
    "en_camino": {"entregado"},
    "entregado": set(),
    "cancelado": set(),
}


class ServicioPedidos:
    def __init__(self, db: Session, usuario: Usuario):
        self.db = db
        self.usuario = usuario
        self.inventario = ServicioInventario(db, usuario)

    def crear_pedido(self, datos: PedidoCrear):
        if not datos.lineas:
            raise HTTPException(status_code=400, detail="El pedido debe incluir productos.")

        cliente = None
        cliente_id = datos.cliente_id
        if self.usuario.rol == "cliente" and self.usuario.cliente_id:
            cliente_id = self.usuario.cliente_id

        if cliente_id:
            cliente = self.db.query(Cliente).filter(
                Cliente.id == cliente_id,
                Cliente.tienda_id == self.usuario.tienda_id,
            ).first()

        nombre = datos.nombre_cliente or (cliente.nombre if cliente else self.usuario.nombre)
        telefono = datos.telefono or (cliente.telefono if cliente else self.usuario.telefono)
        direccion = datos.direccion or (cliente.direccion if cliente else "")
        if not telefono or not direccion:
            raise HTTPException(status_code=400, detail="El pedido necesita teléfono y dirección.")

        lineas_preparadas = []
        subtotal = 0.0
        for linea in datos.lineas:
            producto = self.inventario.obtener_producto(linea.producto_id)
            if producto.cantidad_disponible < linea.cantidad:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para {producto.nombre}.")
            valor = producto.precio_venta * linea.cantidad
            subtotal += valor
            lineas_preparadas.append((producto, linea.cantidad, valor))

        numero = numero_documento("PED")
        pedido = Pedido(
            tienda_id=self.usuario.tienda_id,
            cliente_id=cliente_id,
            usuario_creador_id=self.usuario.id,
            numero=numero,
            nombre_cliente=nombre,
            telefono=telefono,
            direccion=direccion,
            notas=datos.notas,
            subtotal=round(subtotal, 2),
            costo_domicilio=round(datos.costo_domicilio, 2),
            total=round(subtotal + datos.costo_domicilio, 2),
            metodo_pago=datos.metodo_pago,
            estado="recibido",
        )
        self.db.add(pedido)
        self.db.flush()

        # El stock queda reservado desde que el pedido se confirma. Esto evita
        # que otra venta consuma esas mismas unidades mientras el pedido avanza.
        for producto, cantidad, valor in lineas_preparadas:
            self.db.add(DetallePedido(
                pedido_id=pedido.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=producto.precio_venta,
                subtotal=round(valor, 2),
            ))
            self.inventario.cambiar_existencia(producto, -cantidad, "pedido_reserva", numero)

        registrar_actividad(
            self.db, self.usuario.tienda_id, self.usuario.id,
            "pedido_creado", "pedido", pedido.id,
            f"Pedido {numero} creado por ${pedido.total:,.0f}.",
        )
        self.db.commit()
        self.db.refresh(pedido)
        return pedido

    def asignar_domiciliario(self, pedido: Pedido, domiciliario_id: int):
        domiciliario = self.db.query(Usuario).filter(
            Usuario.id == domiciliario_id,
            Usuario.tienda_id == self.usuario.tienda_id,
            Usuario.rol == "domiciliario",
            Usuario.activo.is_(True),
        ).first()
        if not domiciliario:
            raise HTTPException(status_code=400, detail="Domiciliario no válido.")
        if pedido.estado not in {"listo", "en_camino"}:
            raise HTTPException(status_code=400, detail="El pedido debe estar listo antes de asignar ruta.")

        pedido.domiciliario_id = domiciliario.id
        pedido.fecha_actualizacion = datetime.now(timezone.utc)
        registrar_actividad(
            self.db, self.usuario.tienda_id, self.usuario.id,
            "domiciliario_asignado", "pedido", pedido.id,
            f"{domiciliario.nombre} fue asignado al pedido {pedido.numero}.",
        )
        self.db.commit()
        self.db.refresh(pedido)
        return pedido

    def cambiar_estado(self, pedido: Pedido, estado_nuevo: str):
        actual = pedido.estado
        permitidos = TRANSICIONES.get(actual, set())
        if estado_nuevo not in permitidos:
            raise HTTPException(status_code=400, detail=f"No se puede pasar de {actual} a {estado_nuevo}.")

        if self.usuario.rol == "domiciliario":
            if pedido.domiciliario_id != self.usuario.id:
                raise HTTPException(status_code=403, detail="Este pedido no está asignado a ti.")
            if estado_nuevo not in {"en_camino", "entregado"}:
                raise HTTPException(status_code=403, detail="Ese cambio de estado no corresponde al domiciliario.")

        if estado_nuevo == "en_camino" and not pedido.domiciliario_id:
            raise HTTPException(status_code=400, detail="Primero debes asignar un domiciliario.")

        pedido.estado = estado_nuevo
        pedido.fecha_actualizacion = datetime.now(timezone.utc)

        if estado_nuevo == "cancelado":
            self._restaurar_stock(pedido)
        elif estado_nuevo == "entregado":
            self._registrar_venta_del_pedido(pedido)

        registrar_actividad(
            self.db, self.usuario.tienda_id, self.usuario.id,
            "pedido_estado_actualizado", "pedido", pedido.id,
            f"Pedido {pedido.numero}: {actual} → {estado_nuevo}.",
        )
        self.db.commit()
        self.db.refresh(pedido)
        return pedido

    def _restaurar_stock(self, pedido: Pedido):
        detalles = self.db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido.id).all()
        for detalle in detalles:
            producto = self.inventario.obtener_producto(detalle.producto_id)
            self.inventario.cambiar_existencia(
                producto,
                detalle.cantidad,
                "pedido_cancelado",
                pedido.numero,
                "Reposición automática por cancelación.",
            )

    def _registrar_venta_del_pedido(self, pedido: Pedido):
        # El pedido ya reservó el stock. Aquí solo registramos el ingreso para
        # evitar descontar dos veces el inventario.
        venta_existente = self.db.query(Venta).filter(Venta.pedido_id == pedido.id).first()
        if venta_existente:
            return

        detalles = self.db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido.id).all()
        costo_total = 0.0
        numero = numero_documento("VPD")
        venta = Venta(
            tienda_id=pedido.tienda_id,
            usuario_id=self.usuario.id,
            cliente_id=pedido.cliente_id,
            pedido_id=pedido.id,
            numero=numero,
            subtotal=pedido.subtotal,
            descuento=0,
            impuesto=0,
            total=pedido.total,
            metodo_pago=pedido.metodo_pago,
        )
        self.db.add(venta)
        self.db.flush()

        for detalle in detalles:
            producto = self.inventario.obtener_producto(detalle.producto_id)
            costo_total += producto.precio_compra * detalle.cantidad
            self.db.add(DetalleVenta(
                venta_id=venta.id,
                producto_id=producto.id,
                cantidad=detalle.cantidad,
                precio_unitario=detalle.precio_unitario,
                costo_unitario=producto.precio_compra,
                subtotal=detalle.subtotal,
            ))

        venta.costo_total = round(costo_total, 2)
        venta.ganancia_estimada = round(venta.total - costo_total, 2)
