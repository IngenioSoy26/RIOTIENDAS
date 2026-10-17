from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencias import requiere_permiso
from app.database.sesion import obtener_db
from app.esquemas.comunes import VentaCrear
from app.modelos.modelos import Usuario, Venta
from app.servicios.servicio_ventas import ServicioVentas

router = APIRouter(prefix="/api", tags=["Ventas"])


@router.post("/ventas")
def crear_venta(datos: VentaCrear, usuario: Usuario = Depends(requiere_permiso("ventas.crear")), db: Session = Depends(obtener_db)):
    venta = ServicioVentas(db, usuario).crear_venta(datos)
    return {
        "id": venta.id,
        "numero": venta.numero,
        "total": venta.total,
        "ganancia_estimada": venta.ganancia_estimada,
        "metodo_pago": venta.metodo_pago,
    }


@router.get("/ventas")
def listar_ventas(usuario: Usuario = Depends(requiere_permiso("ventas.ver")), db: Session = Depends(obtener_db)):
    filas = db.query(Venta).filter(Venta.tienda_id == usuario.tienda_id).order_by(Venta.fecha.desc()).limit(100).all()
    return [{
        "id": v.id,
        "numero": v.numero,
        "total": v.total,
        "ganancia_estimada": v.ganancia_estimada,
        "metodo_pago": v.metodo_pago,
        "fecha": v.fecha.isoformat(),
        "usuario_id": v.usuario_id,
        "pedido_id": v.pedido_id,
    } for v in filas]
