from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.rutas_autenticacion import router as router_autenticacion
from app.api.rutas_clientes import router as router_clientes
from app.api.rutas_compras import router as router_compras
from app.api.rutas_inventario import router as router_inventario
from app.api.rutas_pedidos import router as router_pedidos
from app.api.rutas_reportes import router as router_reportes
from app.api.rutas_ventas import router as router_ventas
from app.core.configuracion import configuracion
from app.database.base import Base
from app.database.sesion import SesionLocal, motor
from app.seed.cargar_datos import cargar_datos_iniciales


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def ciclo_vida(aplicacion: FastAPI):
    Base.metadata.create_all(bind=motor)
    db = SesionLocal()
    try:
        cargar_datos_iniciales(db)
    finally:
        db.close()
    yield


aplicacion = FastAPI(
    title=configuracion.app_nombre,
    version="1.0.0",
    description="Backend del MVP funcional RIOTIENDAS.",
    lifespan=ciclo_vida,
)

aplicacion.add_middleware(
    CORSMiddleware,
    allow_origins=configuracion.lista_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [
    router_autenticacion,
    router_inventario,
    router_ventas,
    router_compras,
    router_clientes,
    router_pedidos,
    router_reportes,
]:
    aplicacion.include_router(router)

aplicacion.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@aplicacion.get("/", include_in_schema=False)
def interfaz_principal():
    return FileResponse(STATIC_DIR / "index.html")


@aplicacion.get("/manifest.json", include_in_schema=False)
def manifest():
    return FileResponse(STATIC_DIR / "manifest.json", media_type="application/manifest+json")


@aplicacion.get("/sw.js", include_in_schema=False)
def service_worker():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")
