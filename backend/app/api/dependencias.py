from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from app.core.configuracion import configuracion
from app.core.seguridad import tiene_permiso
from app.database.sesion import obtener_db
from app.modelos.modelos import Usuario


oauth2 = OAuth2PasswordBearer(tokenUrl="/api/autenticacion/ingresar")


def obtener_usuario_actual(token: str = Depends(oauth2), db: Session = Depends(obtener_db)) -> Usuario:
    try:
        carga = jwt.decode(token, configuracion.app_llave_secreta, algorithms=[configuracion.app_algoritmo_jwt])
        usuario_id = int(carga.get("sub"))
    except Exception as error:
        raise HTTPException(status_code=401, detail="Sesión inválida o vencida.") from error

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.activo.is_(True)).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no disponible.")
    return usuario


def requiere_permiso(permiso: str):
    def dependencia(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
        if not tiene_permiso(usuario.rol, usuario.permisos_personalizados, permiso):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para realizar esta acción ({permiso}).",
            )
        return usuario
    return dependencia
