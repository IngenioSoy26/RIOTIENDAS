from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modelos.modelos import Actividad


def registrar_actividad(
    db: Session,
    tienda_id: int,
    usuario_id: int | None,
    accion: str,
    entidad: str = "",
    entidad_id: int | None = None,
    detalle: str = "",
):
    db.add(Actividad(
        tienda_id=tienda_id,
        usuario_id=usuario_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=detalle,
    ))


def numero_documento(prefijo: str) -> str:
    ahora = datetime.now(timezone.utc)
    return f"{prefijo}-{ahora:%Y%m%d%H%M%S%f}"
