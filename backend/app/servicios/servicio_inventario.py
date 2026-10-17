from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modelos.modelos import MovimientoInventario, Producto, Usuario


class ServicioInventario:
    """Reglas de inventario usadas por ventas, compras, ajustes y pedidos."""

    def __init__(self, db: Session, usuario: Usuario):
        self.db = db
        self.usuario = usuario

    def listar_productos(self, buscar: str = "", solo_activos: bool = True):
        consulta = self.db.query(Producto).filter(Producto.tienda_id == self.usuario.tienda_id)
        if solo_activos:
            consulta = consulta.filter(Producto.activo.is_(True))
        if buscar:
            patron = f"%{buscar}%"
            consulta = consulta.filter(or_(
                Producto.nombre.ilike(patron),
                Producto.codigo_barras.ilike(patron),
                Producto.codigo_interno.ilike(patron),
                Producto.marca.ilike(patron),
            ))
        return consulta.order_by(Producto.nombre).all()

    def obtener_producto(self, producto_id: int) -> Producto:
        producto = self.db.query(Producto).filter(
            Producto.id == producto_id,
            Producto.tienda_id == self.usuario.tienda_id,
        ).first()
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado.")
        return producto

    def obtener_por_codigo(self, codigo: str) -> Producto:
        producto = self.db.query(Producto).filter(
            Producto.tienda_id == self.usuario.tienda_id,
            or_(Producto.codigo_barras == codigo, Producto.codigo_interno == codigo),
            Producto.activo.is_(True),
        ).first()
        if not producto:
            raise HTTPException(status_code=404, detail="Código no registrado.")
        return producto

    def cambiar_existencia(self, producto: Producto, cantidad: float, tipo: str, referencia: str, nota: str = ""):
        anterior = producto.cantidad_disponible
        nueva = round(anterior + cantidad, 3)
        if nueva < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {producto.nombre}. Disponible: {anterior}.",
            )

        producto.cantidad_disponible = nueva
        self.db.add(MovimientoInventario(
            tienda_id=self.usuario.tienda_id,
            producto_id=producto.id,
            usuario_id=self.usuario.id,
            tipo=tipo,
            cantidad=cantidad,
            existencia_anterior=anterior,
            existencia_nueva=nueva,
            referencia=referencia,
            nota=nota,
        ))

    def alertas(self):
        productos = self.listar_productos()
        hoy = date.today()
        limite_vencimiento = hoy + timedelta(days=30)
        alertas = []

        for producto in productos:
            if producto.cantidad_disponible <= 0:
                alertas.append({
                    "nivel": "critico", "tipo": "agotado", "producto_id": producto.id,
                    "mensaje": f"{producto.nombre}: producto agotado.",
                })
            elif producto.cantidad_disponible <= producto.stock_minimo:
                alertas.append({
                    "nivel": "advertencia", "tipo": "stock_bajo", "producto_id": producto.id,
                    "mensaje": f"{producto.nombre}: quedan {producto.cantidad_disponible:g} {producto.unidad_medida}(s).",
                })

            if producto.fecha_vencimiento and hoy <= producto.fecha_vencimiento <= limite_vencimiento:
                dias = (producto.fecha_vencimiento - hoy).days
                alertas.append({
                    "nivel": "advertencia", "tipo": "vencimiento", "producto_id": producto.id,
                    "mensaje": f"{producto.nombre}: vence en {dias} día(s).",
                })

        return alertas
