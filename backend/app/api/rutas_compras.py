from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencias import requiere_permiso
from app.database.sesion import obtener_db
from app.esquemas.comunes import CompraCrear, ProveedorEntrada
from app.modelos.modelos import Compra, Proveedor, Usuario
from app.servicios.servicio_compras import ServicioCompras
from app.servicios.utilidades import registrar_actividad

router = APIRouter(prefix="/api", tags=["Compras y proveedores"])


@router.get("/proveedores")
def listar_proveedores(usuario: Usuario = Depends(requiere_permiso("proveedores.ver")), db: Session = Depends(obtener_db)):
    filas = db.query(Proveedor).filter(
        Proveedor.tienda_id == usuario.tienda_id,
        Proveedor.activo.is_(True),
    ).order_by(Proveedor.nombre).all()
    return [{
        "id": p.id,
        "nombre": p.nombre,
        "telefono": p.telefono,
        "direccion": p.direccion,
        "correo": p.correo,
        "notas": p.notas,
    } for p in filas]


@router.post("/proveedores")
def crear_proveedor(datos: ProveedorEntrada, usuario: Usuario = Depends(requiere_permiso("proveedores.crear")), db: Session = Depends(obtener_db)):
    proveedor = Proveedor(tienda_id=usuario.tienda_id, **datos.model_dump())
    db.add(proveedor)
    db.flush()
    registrar_actividad(db, usuario.tienda_id, usuario.id, "proveedor_creado", "proveedor", proveedor.id, proveedor.nombre)
    db.commit()
    return {"id": proveedor.id, **datos.model_dump()}


@router.post("/compras")
def crear_compra(datos: CompraCrear, usuario: Usuario = Depends(requiere_permiso("compras.crear")), db: Session = Depends(obtener_db)):
    compra = ServicioCompras(db, usuario).crear_compra(datos)
    return {
        "id": compra.id,
        "numero": compra.numero,
        "total": compra.total,
        "fecha": compra.fecha.isoformat(),
    }


@router.get("/compras")
def listar_compras(usuario: Usuario = Depends(requiere_permiso("compras.ver")), db: Session = Depends(obtener_db)):
    filas = db.query(Compra).filter(Compra.tienda_id == usuario.tienda_id).order_by(Compra.fecha.desc()).limit(100).all()
    return [{
        "id": c.id,
        "numero": c.numero,
        "proveedor_id": c.proveedor_id,
        "total": c.total,
        "observacion": c.observacion,
        "fecha": c.fecha.isoformat(),
    } for c in filas]
