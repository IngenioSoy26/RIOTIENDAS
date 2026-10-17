from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencias import requiere_permiso
from app.database.sesion import obtener_db
from app.esquemas.comunes import ClienteEntrada
from app.modelos.modelos import Cliente, Usuario
from app.servicios.utilidades import registrar_actividad

router = APIRouter(prefix="/api", tags=["Clientes"])


@router.get("/clientes")
def listar_clientes(usuario: Usuario = Depends(requiere_permiso("clientes.ver")), db: Session = Depends(obtener_db)):
    filas = db.query(Cliente).filter(
        Cliente.tienda_id == usuario.tienda_id,
        Cliente.activo.is_(True),
    ).order_by(Cliente.nombre).all()
    return [{
        "id": c.id,
        "nombre": c.nombre,
        "telefono": c.telefono,
        "direccion": c.direccion,
        "correo": c.correo,
    } for c in filas]


@router.post("/clientes")
def crear_cliente(datos: ClienteEntrada, usuario: Usuario = Depends(requiere_permiso("clientes.crear")), db: Session = Depends(obtener_db)):
    cliente = Cliente(tienda_id=usuario.tienda_id, **datos.model_dump())
    db.add(cliente)
    db.flush()
    registrar_actividad(db, usuario.tienda_id, usuario.id, "cliente_creado", "cliente", cliente.id, cliente.nombre)
    db.commit()
    return {"id": cliente.id, **datos.model_dump()}
