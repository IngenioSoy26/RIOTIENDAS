from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencias import obtener_usuario_actual, requiere_permiso
from app.api.serializadores import producto_diccionario
from app.core.seguridad import obtener_permisos_efectivos
from app.database.sesion import obtener_db
from app.esquemas.comunes import AjusteInventario, CategoriaEntrada, ProductoEntrada
from app.modelos.modelos import Categoria, MovimientoInventario, Producto, Usuario
from app.servicios.servicio_inventario import ServicioInventario
from app.servicios.utilidades import registrar_actividad

router = APIRouter(prefix="/api", tags=["Productos e inventario"])


@router.get("/categorias")
def listar_categorias(usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)):
    filas = db.query(Categoria).filter(Categoria.tienda_id == usuario.tienda_id).order_by(Categoria.nombre).all()
    return [{"id": c.id, "nombre": c.nombre, "descripcion": c.descripcion} for c in filas]


@router.post("/categorias")
def crear_categoria(datos: CategoriaEntrada, usuario: Usuario = Depends(requiere_permiso("productos.crear")), db: Session = Depends(obtener_db)):
    existente = db.query(Categoria).filter(
        Categoria.tienda_id == usuario.tienda_id,
        Categoria.nombre.ilike(datos.nombre),
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="La categoría ya existe.")
    categoria = Categoria(tienda_id=usuario.tienda_id, nombre=datos.nombre, descripcion=datos.descripcion)
    db.add(categoria)
    db.flush()
    registrar_actividad(db, usuario.tienda_id, usuario.id, "categoria_creada", "categoria", categoria.id, categoria.nombre)
    db.commit()
    return {"id": categoria.id, "nombre": categoria.nombre, "descripcion": categoria.descripcion}


@router.get("/productos")
def listar_productos(buscar: str = "", usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)):
    permisos = obtener_permisos_efectivos(usuario.rol, usuario.permisos_personalizados)
    if "*" not in permisos and "productos.ver" not in permisos and "catalogo.ver" not in permisos:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver productos.")
    return [producto_diccionario(p) for p in ServicioInventario(db, usuario).listar_productos(buscar)]


@router.get("/productos/codigo/{codigo}")
def producto_por_codigo(codigo: str, usuario: Usuario = Depends(requiere_permiso("productos.ver")), db: Session = Depends(obtener_db)):
    producto = ServicioInventario(db, usuario).obtener_por_codigo(codigo)
    return producto_diccionario(producto)


@router.post("/productos")
def crear_producto(datos: ProductoEntrada, usuario: Usuario = Depends(requiere_permiso("productos.crear")), db: Session = Depends(obtener_db)):
    fecha_vencimiento = date.fromisoformat(datos.fecha_vencimiento) if datos.fecha_vencimiento else None
    if datos.codigo_barras and db.query(Producto).filter(
        Producto.tienda_id == usuario.tienda_id,
        Producto.codigo_barras == datos.codigo_barras,
    ).first():
        raise HTTPException(status_code=400, detail="Ya existe un producto con ese código de barras.")

    producto = Producto(
        tienda_id=usuario.tienda_id,
        nombre=datos.nombre,
        codigo_barras=datos.codigo_barras,
        codigo_interno=datos.codigo_interno,
        categoria_id=datos.categoria_id,
        proveedor_id=datos.proveedor_id,
        marca=datos.marca,
        precio_compra=datos.precio_compra,
        precio_venta=datos.precio_venta,
        cantidad_disponible=datos.cantidad_disponible,
        stock_minimo=datos.stock_minimo,
        unidad_medida=datos.unidad_medida,
        fecha_vencimiento=fecha_vencimiento,
        imagen_url=datos.imagen_url,
    )
    db.add(producto)
    db.flush()
    registrar_actividad(db, usuario.tienda_id, usuario.id, "producto_creado", "producto", producto.id, producto.nombre)
    db.commit()
    db.refresh(producto)
    return producto_diccionario(producto)


@router.put("/productos/{producto_id}")
def editar_producto(producto_id: int, datos: ProductoEntrada, usuario: Usuario = Depends(requiere_permiso("productos.editar")), db: Session = Depends(obtener_db)):
    producto = ServicioInventario(db, usuario).obtener_producto(producto_id)
    for campo in [
        "nombre", "codigo_barras", "codigo_interno", "categoria_id", "proveedor_id",
        "marca", "precio_compra", "precio_venta", "stock_minimo", "unidad_medida", "imagen_url",
    ]:
        setattr(producto, campo, getattr(datos, campo))
    producto.fecha_vencimiento = date.fromisoformat(datos.fecha_vencimiento) if datos.fecha_vencimiento else None
    registrar_actividad(db, usuario.tienda_id, usuario.id, "producto_editado", "producto", producto.id, producto.nombre)
    db.commit()
    return producto_diccionario(producto)


@router.post("/inventario/{producto_id}/ajustar")
def ajustar_inventario(producto_id: int, datos: AjusteInventario, usuario: Usuario = Depends(requiere_permiso("inventario.ajustar")), db: Session = Depends(obtener_db)):
    servicio = ServicioInventario(db, usuario)
    producto = servicio.obtener_producto(producto_id)
    servicio.cambiar_existencia(producto, datos.cantidad, "ajuste", "AJUSTE-MANUAL", datos.nota)
    registrar_actividad(db, usuario.tienda_id, usuario.id, "inventario_ajustado", "producto", producto.id, f"Ajuste {datos.cantidad:+g}. {datos.nota}")
    db.commit()
    return producto_diccionario(producto)


@router.get("/inventario/movimientos")
def movimientos_inventario(usuario: Usuario = Depends(requiere_permiso("inventario.ver")), db: Session = Depends(obtener_db)):
    filas = db.query(MovimientoInventario).filter(
        MovimientoInventario.tienda_id == usuario.tienda_id
    ).order_by(MovimientoInventario.fecha.desc()).limit(100).all()
    return [{
        "id": m.id,
        "producto_id": m.producto_id,
        "tipo": m.tipo,
        "cantidad": m.cantidad,
        "existencia_anterior": m.existencia_anterior,
        "existencia_nueva": m.existencia_nueva,
        "referencia": m.referencia,
        "nota": m.nota,
        "fecha": m.fecha.isoformat(),
    } for m in filas]


@router.get("/alertas")
def alertas(usuario: Usuario = Depends(requiere_permiso("alertas.ver")), db: Session = Depends(obtener_db)):
    return ServicioInventario(db, usuario).alertas()
