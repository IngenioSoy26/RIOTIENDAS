from datetime import datetime, timezone
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.dependencias import obtener_usuario_actual, requiere_permiso
from app.api.serializadores import pedido_diccionario, producto_diccionario
from app.database.sesion import obtener_db
from app.esquemas.comunes import GastoCrear
from app.modelos.modelos import Actividad, Cliente, Compra, Gasto, Pedido, Producto, Proveedor, Tienda, Usuario, Venta
from app.servicios.servicio_reportes import ServicioReportes
from app.servicios.utilidades import registrar_actividad

router = APIRouter(prefix="/api", tags=["Dashboard, reportes y utilidades"])


@router.get("/salud")
def salud():
    return {"estado": "ok", "aplicacion": "RIOTIENDAS"}


@router.get("/dashboard")
def dashboard(usuario: Usuario = Depends(requiere_permiso("dashboard.ver")), db: Session = Depends(obtener_db)):
    return ServicioReportes(db, usuario).resumen_dashboard()


@router.post("/gastos")
def crear_gasto(datos: GastoCrear, usuario: Usuario = Depends(requiere_permiso("gastos.crear")), db: Session = Depends(obtener_db)):
    gasto = Gasto(tienda_id=usuario.tienda_id, usuario_id=usuario.id, **datos.model_dump())
    db.add(gasto)
    db.flush()
    registrar_actividad(db, usuario.tienda_id, usuario.id, "gasto_creado", "gasto", gasto.id, f"{gasto.concepto}: ${gasto.valor:,.0f}")
    db.commit()
    return {"id": gasto.id, **datos.model_dump()}


@router.get("/reportes/resumen")
def reporte_resumen(usuario: Usuario = Depends(requiere_permiso("reportes.ver")), db: Session = Depends(obtener_db)):
    servicio = ServicioReportes(db, usuario)
    resumen = servicio.resumen_dashboard()
    total_compras = float(db.query(func.coalesce(func.sum(Compra.total), 0)).filter(Compra.tienda_id == usuario.tienda_id).scalar() or 0)
    total_gastos = float(db.query(func.coalesce(func.sum(Gasto.valor), 0)).filter(Gasto.tienda_id == usuario.tienda_id).scalar() or 0)
    ventas = db.query(Venta).filter(Venta.tienda_id == usuario.tienda_id, Venta.anulada.is_(False)).all()
    resumen.update({
        "total_historico_ventas": round(sum(v.total for v in ventas), 2),
        "total_historico_ganancia": round(sum(v.ganancia_estimada for v in ventas), 2),
        "total_compras": round(total_compras, 2),
        "total_gastos": round(total_gastos, 2),
    })
    return resumen


@router.get("/reportes/exportar/{formato}")
def exportar_reporte(formato: str, usuario: Usuario = Depends(requiere_permiso("reportes.ver")), db: Session = Depends(obtener_db)):
    servicio = ServicioReportes(db, usuario)
    if formato == "csv":
        return Response(
            servicio.exportar_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=ventas_riotiendas.csv"},
        )
    if formato == "xlsx":
        return Response(
            servicio.exportar_excel(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=ventas_riotiendas.xlsx"},
        )
    if formato == "pdf":
        return Response(
            servicio.exportar_pdf(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=ventas_riotiendas.pdf"},
        )
    raise HTTPException(status_code=400, detail="Formato no soportado.")


@router.get("/historial")
def historial(usuario: Usuario = Depends(requiere_permiso("historial.ver")), db: Session = Depends(obtener_db)):
    filas = db.query(Actividad).filter(Actividad.tienda_id == usuario.tienda_id).order_by(Actividad.fecha.desc()).limit(200).all()
    usuarios = {u.id: u.nombre for u in db.query(Usuario).filter(Usuario.tienda_id == usuario.tienda_id).all()}
    return [{
        "id": a.id,
        "usuario": usuarios.get(a.usuario_id, "Sistema"),
        "accion": a.accion,
        "entidad": a.entidad,
        "entidad_id": a.entidad_id,
        "detalle": a.detalle,
        "fecha": a.fecha.isoformat(),
    } for a in filas]


@router.get("/buscar")
def buscar_global(q: str = Query(min_length=2), usuario: Usuario = Depends(requiere_permiso("busqueda.usar")), db: Session = Depends(obtener_db)):
    patron = f"%{q}%"
    resultados = []

    for p in db.query(Producto).filter(
        Producto.tienda_id == usuario.tienda_id,
        or_(Producto.nombre.ilike(patron), Producto.codigo_barras.ilike(patron), Producto.codigo_interno.ilike(patron)),
    ).limit(8):
        resultados.append({
            "tipo": "producto", "id": p.id, "titulo": p.nombre,
            "subtitulo": f"Stock {p.cantidad_disponible:g} | ${p.precio_venta:,.0f}",
        })

    for c in db.query(Cliente).filter(
        Cliente.tienda_id == usuario.tienda_id,
        or_(Cliente.nombre.ilike(patron), Cliente.telefono.ilike(patron)),
    ).limit(5):
        resultados.append({"tipo": "cliente", "id": c.id, "titulo": c.nombre, "subtitulo": c.telefono})

    for p in db.query(Proveedor).filter(
        Proveedor.tienda_id == usuario.tienda_id,
        Proveedor.nombre.ilike(patron),
    ).limit(5):
        resultados.append({"tipo": "proveedor", "id": p.id, "titulo": p.nombre, "subtitulo": p.telefono})

    for p in db.query(Pedido).filter(
        Pedido.tienda_id == usuario.tienda_id,
        or_(Pedido.numero.ilike(patron), Pedido.nombre_cliente.ilike(patron)),
    ).limit(5):
        resultados.append({"tipo": "pedido", "id": p.id, "titulo": p.numero, "subtitulo": f"{p.nombre_cliente} | {p.estado}"})

    return resultados


@router.get("/respaldo")
def generar_respaldo(usuario: Usuario = Depends(requiere_permiso("respaldo.generar")), db: Session = Depends(obtener_db)):
    tienda_id = usuario.tienda_id
    contenido = {
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "tienda_id": tienda_id,
        "productos": [producto_diccionario(p) for p in db.query(Producto).filter(Producto.tienda_id == tienda_id).all()],
        "clientes": [{"id": c.id, "nombre": c.nombre, "telefono": c.telefono, "direccion": c.direccion, "correo": c.correo} for c in db.query(Cliente).filter(Cliente.tienda_id == tienda_id).all()],
        "proveedores": [{"id": p.id, "nombre": p.nombre, "telefono": p.telefono, "direccion": p.direccion, "correo": p.correo} for p in db.query(Proveedor).filter(Proveedor.tienda_id == tienda_id).all()],
        "ventas": [{"id": v.id, "numero": v.numero, "total": v.total, "fecha": v.fecha.isoformat()} for v in db.query(Venta).filter(Venta.tienda_id == tienda_id).all()],
        "compras": [{"id": c.id, "numero": c.numero, "total": c.total, "fecha": c.fecha.isoformat()} for c in db.query(Compra).filter(Compra.tienda_id == tienda_id).all()],
        "pedidos": [pedido_diccionario(db, p) for p in db.query(Pedido).filter(Pedido.tienda_id == tienda_id).all()],
    }
    datos = json.dumps(contenido, ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        datos,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=respaldo_riotiendas.json"},
    )


@router.get("/configuracion/tienda")
def ver_tienda(usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)):
    tienda = db.get(Tienda, usuario.tienda_id)
    return {
        "id": tienda.id,
        "nombre": tienda.nombre,
        "nit": tienda.nit,
        "telefono": tienda.telefono,
        "direccion": tienda.direccion,
        "correo": tienda.correo,
        "moneda": tienda.moneda,
        "impuesto_porcentaje": tienda.impuesto_porcentaje,
    }
