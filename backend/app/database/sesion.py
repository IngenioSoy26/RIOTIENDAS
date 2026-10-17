from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.configuracion import configuracion


argumentos = {"check_same_thread": False} if configuracion.app_url_bd.startswith("sqlite") else {}
motor = create_engine(configuracion.app_url_bd, connect_args=argumentos)
SesionLocal = sessionmaker(bind=motor, autocommit=False, autoflush=False)


def obtener_db():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()
