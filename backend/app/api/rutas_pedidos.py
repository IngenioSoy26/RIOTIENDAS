from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencias import obtener_usuario_actual, requiere_permiso
from app.api.serializadores import pedido_diccionario
from app.core.seguridad import obtener_permisos_efectivos
from app.database.sesion import obtener_db
from app.esquemas.comunes import PedidoAsignar, PedidoCrear, PedidoEstado
from app.modelos.modelos import Pedido, Usuario
from app.servicios.servicio_pedidos import ServicioPedidos

router = APIRouter(prefix="/api", tags=["Pedidos y domicilios"])


@router.post("/pedidos")
def crear_pedido(datos: PedidoCrear, usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)):
    permisos = obtener_permisos_efectivos(usuario.rol, usuario.permisos_personalizados)
    if "*" not in permisos and "pedidos.crear" not in permisos and "pedidos.crear_cliente" not in permisos:
        raise HTTPException(status_code=403, detail="No tienes permiso para crear pedidos.")
    pedido = ServicioPedidos(db, usuario).crear_pedido(datos)
    return pedido_diccionario(db, pedido)


@router.get("/pedidos")
def listar_pedidos(usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)):
    if usuario.rol == "cliente":
        filas = db.query(Pedido).filter(
            Pedido.tienda_id == usuario.tienda_id,
            Pedido.cliente_id == usuario.cliente_id,
        ).order_by(Pedido.fecha.desc()).all()
    elif usuario.rol == "domiciliario":
        filas = db.query(Pedido).filter(
            Pedido.tienda_id == usuario.tienda_id,
            Pedido.domiciliario_id == usuario.id,
        ).order_by(Pedido.fecha.desc()).all()
    else:
        permisos = obtener_permisos_efectivos(usuario.rol, usuario.permisos_personalizados)
        if "*" not in permisos and "pedidos.ver" not in permisos:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver pedidos.")
        filas = db.query(Pedido).filter(Pedido.tienda_id == usuario.tienda_id).order_by(Pedido.fecha.desc()).all()

    return [pedido_diccionario(db, pedido) for pedido in filas]


@router.post("/pedidos/{pedido_id}/asignar")
def asignar_pedido(pedido_id: int, datos: PedidoAsignar, usuario: Usuario = Depends(requiere_permiso("pedidos.asignar")), db: Session = Depends(obtener_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id, Pedido.tienda_id == usuario.tienda_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    ServicioPedidos(db, usuario).asignar_domiciliario(pedido, datos.domiciliario_id)
    return pedido_diccionario(db, pedido)


@router.post("/pedidos/{pedido_id}/estado")
def cambiar_estado_pedido(pedido_id: int, datos: PedidoEstado, usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id, Pedido.tienda_id == usuario.tienda_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")

    permisos = obtener_permisos_efectivos(usuario.rol, usuario.permisos_personalizados)
    if usuario.rol != "domiciliario" and "*" not in permisos and "pedidos.preparar" not in permisos:
        raise HTTPException(status_code=403, detail="No tienes permiso para cambiar el estado.")

    ServicioPedidos(db, usuario).cambiar_estado(pedido, datos.estado)
    return pedido_diccionario(db, pedido)


@router.get("/domiciliarios")
def listar_domiciliarios(usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)):
    filas = db.query(Usuario).filter(
        Usuario.tienda_id == usuario.tienda_id,
        Usuario.rol == "domiciliario",
        Usuario.activo.is_(True),
    ).all()
    return [{"id": u.id, "nombre": u.nombre, "telefono": u.telefono} for u in filas]
