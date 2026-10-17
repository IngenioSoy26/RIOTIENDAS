from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import os

import jwt

from app.core.configuracion import configuracion


PERMISOS_POR_ROL = {
    "administrador": ["*"],
    "cajero": [
        "dashboard.ver", "ventas.ver", "ventas.crear", "productos.ver",
        "inventario.ver", "clientes.ver", "clientes.crear", "pedidos.ver",
        "pedidos.crear", "reportes.ver", "busqueda.usar",
    ],
    "empleado": [
        "dashboard.ver", "productos.ver", "inventario.ver", "inventario.ajustar",
        "pedidos.ver", "pedidos.preparar", "compras.ver", "compras.crear",
        "proveedores.ver", "alertas.ver", "busqueda.usar",
    ],
    "domiciliario": ["dashboard.ver", "pedidos.propios", "pedidos.entregar"],
    "cliente": ["catalogo.ver", "pedidos.crear_cliente", "pedidos.propios_cliente"],
}


def crear_hash_contrasena(contrasena: str) -> str:
    """Crea un hash PBKDF2 con sal aleatoria."""
    sal = os.urandom(16)
    derivado = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), sal, 160000)
    return f"{base64.b64encode(sal).decode()}${base64.b64encode(derivado).decode()}"


def verificar_contrasena(contrasena: str, valor_guardado: str) -> bool:
    try:
        sal_texto, hash_texto = valor_guardado.split("$", 1)
        sal = base64.b64decode(sal_texto)
        derivado = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), sal, 160000)
        return hmac.compare_digest(base64.b64encode(derivado).decode(), hash_texto)
    except Exception:
        return False


def crear_token_acceso(usuario_id: int, tienda_id: int, rol: str) -> str:
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=configuracion.app_expiracion_token_minutos)
    carga = {"sub": str(usuario_id), "tienda_id": tienda_id, "rol": rol, "exp": expiracion}
    return jwt.encode(carga, configuracion.app_llave_secreta, algorithm=configuracion.app_algoritmo_jwt)


def obtener_permisos_efectivos(rol: str, permisos_personalizados: str | None) -> list[str]:
    """Si existen permisos personalizados, reemplazan los predeterminados del rol."""
    if permisos_personalizados:
        try:
            permisos = json.loads(permisos_personalizados)
            if isinstance(permisos, list):
                return permisos
        except json.JSONDecodeError:
            pass
    return PERMISOS_POR_ROL.get(rol, [])


def tiene_permiso(rol: str, permisos_personalizados: str | None, permiso: str) -> bool:
    permisos = obtener_permisos_efectivos(rol, permisos_personalizados)
    return "*" in permisos or permiso in permisos


def crear_token_recuperacion(usuario_id: int) -> str:
    """Token corto utilizado únicamente para restablecer una contraseña."""
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=20)
    carga = {"sub": str(usuario_id), "proposito": "recuperar_contrasena", "exp": expiracion}
    return jwt.encode(carga, configuracion.app_llave_secreta, algorithm=configuracion.app_algoritmo_jwt)


def validar_token_recuperacion(token: str) -> int:
    """Valida un token de recuperación y retorna el id del usuario."""
    carga = jwt.decode(token, configuracion.app_llave_secreta, algorithms=[configuracion.app_algoritmo_jwt])
    if carga.get("proposito") != "recuperar_contrasena":
        raise jwt.InvalidTokenError("Propósito de token inválido")
    return int(carga["sub"])
