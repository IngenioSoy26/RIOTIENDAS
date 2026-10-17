import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencias import obtener_usuario_actual, requiere_permiso
from app.core.seguridad import (
    PERMISOS_POR_ROL, crear_hash_contrasena, crear_token_acceso, crear_token_recuperacion,
    obtener_permisos_efectivos, validar_token_recuperacion, verificar_contrasena,
)
from app.database.sesion import obtener_db
from app.esquemas.comunes import (
    Credenciales, RecuperacionSolicitud, RestablecerContrasena, TiendaRegistro,
    UsuarioCrear, UsuarioPermisosActualizar,
)
from app.modelos.modelos import Cliente, Tienda, Usuario
from app.servicios.utilidades import registrar_actividad
from app.core.configuracion import configuracion

router = APIRouter(prefix="/api", tags=["Autenticación y usuarios"])




@router.post("/autenticacion/registrar-tienda")
def registrar_tienda(datos: TiendaRegistro, db: Session = Depends(obtener_db)):
    """Registro inicial del negocio y de su primer administrador.

    Esta ruta permite que el prototipo pueda arrancar desde cero sin depender
    de datos precargados.
    """
    if db.query(Usuario).filter(Usuario.correo == datos.correo).first():
        raise HTTPException(status_code=400, detail="Ese correo ya está registrado.")

    tienda = Tienda(
        nombre=datos.nombre_tienda,
        telefono=datos.telefono,
        direccion=datos.direccion,
        correo=str(datos.correo),
        moneda="COP",
        impuesto_porcentaje=0,
    )
    db.add(tienda)
    db.flush()

    administrador = Usuario(
        tienda_id=tienda.id,
        nombre=datos.nombre_administrador,
        correo=str(datos.correo),
        telefono=datos.telefono,
        contrasena_hash=crear_hash_contrasena(datos.contrasena),
        rol="administrador",
    )
    db.add(administrador)
    db.flush()
    registrar_actividad(db, tienda.id, administrador.id, "tienda_creada", "tienda", tienda.id, tienda.nombre)
    db.commit()

    token = crear_token_acceso(administrador.id, tienda.id, administrador.rol)
    return {"access_token": token, "token_type": "bearer", "tienda_id": tienda.id}


@router.post("/autenticacion/solicitar-recuperacion")
def solicitar_recuperacion(datos: RecuperacionSolicitud, db: Session = Depends(obtener_db)):
    usuario = db.query(Usuario).filter(Usuario.correo == datos.correo, Usuario.activo.is_(True)).first()
    respuesta = {
        "mensaje": "Si el correo existe, se generó una solicitud de recuperación.",
    }
    if usuario:
        token = crear_token_recuperacion(usuario.id)
        # En producción este token debe enviarse por correo y no devolverse al navegador.
        # En modo demo sí se muestra para que el flujo pueda probarse de principio a fin.
        if configuracion.app_ambiente != "produccion":
            respuesta["token_demo"] = token
    return respuesta


@router.post("/autenticacion/restablecer-contrasena")
def restablecer_contrasena(datos: RestablecerContrasena, db: Session = Depends(obtener_db)):
    try:
        usuario_id = validar_token_recuperacion(datos.token)
    except Exception as error:
        raise HTTPException(status_code=400, detail="El enlace de recuperación no es válido o expiró.") from error

    usuario = db.get(Usuario, usuario_id)
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    usuario.contrasena_hash = crear_hash_contrasena(datos.nueva_contrasena)
    registrar_actividad(db, usuario.tienda_id, usuario.id, "contrasena_restaurada", "usuario", usuario.id, "Contraseña restablecida.")
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente."}


@router.post("/autenticacion/ingresar")
def ingresar(datos: Credenciales, db: Session = Depends(obtener_db)):
    usuario = db.query(Usuario).filter(Usuario.correo == datos.correo, Usuario.activo.is_(True)).first()
    if not usuario or not verificar_contrasena(datos.contrasena, usuario.contrasena_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

    token = crear_token_acceso(usuario.id, usuario.tienda_id, usuario.rol)
    registrar_actividad(db, usuario.tienda_id, usuario.id, "inicio_sesion", "usuario", usuario.id, "Inicio de sesión correcto.")
    db.commit()
    return {"access_token": token, "token_type": "bearer"}


@router.get("/autenticacion/yo")
def mi_perfil(usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)):
    tienda = db.get(Tienda, usuario.tienda_id)
    cliente = db.get(Cliente, usuario.cliente_id) if usuario.cliente_id else None
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "telefono": usuario.telefono,
        "rol": usuario.rol,
        "tienda_id": usuario.tienda_id,
        "cliente_id": usuario.cliente_id,
        "cliente": {
            "nombre": cliente.nombre,
            "telefono": cliente.telefono,
            "direccion": cliente.direccion,
        } if cliente else None,
        "tienda": {
            "id": tienda.id,
            "nombre": tienda.nombre,
            "direccion": tienda.direccion,
        } if tienda else None,
        "permisos": obtener_permisos_efectivos(usuario.rol, usuario.permisos_personalizados),
    }


@router.get("/usuarios")
def listar_usuarios(usuario: Usuario = Depends(requiere_permiso("usuarios.ver")), db: Session = Depends(obtener_db)):
    usuarios = db.query(Usuario).filter(Usuario.tienda_id == usuario.tienda_id).order_by(Usuario.nombre).all()
    return [{
        "id": item.id,
        "nombre": item.nombre,
        "correo": item.correo,
        "telefono": item.telefono,
        "rol": item.rol,
        "activo": item.activo,
        "permisos": obtener_permisos_efectivos(item.rol, item.permisos_personalizados),
    } for item in usuarios]


@router.post("/usuarios")
def crear_usuario(datos: UsuarioCrear, usuario: Usuario = Depends(requiere_permiso("usuarios.crear")), db: Session = Depends(obtener_db)):
    if datos.rol not in PERMISOS_POR_ROL:
        raise HTTPException(status_code=400, detail="Rol no válido.")
    if db.query(Usuario).filter(Usuario.correo == datos.correo).first():
        raise HTTPException(status_code=400, detail="Ese correo ya está registrado.")

    # Un usuario con rol "cliente" necesita un registro de cliente asociado para
    # poder comprar y ver sus propios pedidos; sin ese enlace el flujo de la
    # tienda queda inutilizable en una tienda creada desde cero.
    cliente_id = None
    if datos.rol == "cliente":
        cliente = Cliente(
            tienda_id=usuario.tienda_id,
            nombre=datos.nombre,
            telefono=datos.telefono,
            direccion=datos.direccion,
            correo=str(datos.correo),
        )
        db.add(cliente)
        db.flush()
        cliente_id = cliente.id

    nuevo = Usuario(
        tienda_id=usuario.tienda_id,
        cliente_id=cliente_id,
        nombre=datos.nombre,
        correo=datos.correo,
        telefono=datos.telefono,
        contrasena_hash=crear_hash_contrasena(datos.contrasena),
        rol=datos.rol,
    )
    db.add(nuevo)
    db.flush()
    registrar_actividad(db, usuario.tienda_id, usuario.id, "usuario_creado", "usuario", nuevo.id, f"Usuario {nuevo.nombre} con rol {nuevo.rol}.")
    db.commit()
    return {"id": nuevo.id, "mensaje": "Usuario creado."}


@router.put("/usuarios/{usuario_id}/permisos")
def actualizar_permisos(usuario_id: int, datos: UsuarioPermisosActualizar, usuario: Usuario = Depends(requiere_permiso("usuarios.permisos")), db: Session = Depends(obtener_db)):
    objetivo = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.tienda_id == usuario.tienda_id).first()
    if not objetivo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    objetivo.permisos_personalizados = json.dumps(datos.permisos) if datos.permisos is not None else None
    registrar_actividad(db, usuario.tienda_id, usuario.id, "permisos_actualizados", "usuario", objetivo.id, f"Permisos actualizados para {objetivo.nombre}.")
    db.commit()
    return {
        "mensaje": "Permisos actualizados.",
        "permisos": obtener_permisos_efectivos(objetivo.rol, objetivo.permisos_personalizados),
    }
