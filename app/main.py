"""Punto de entrada de la aplicación FastAPI."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.alembic_runner import run_alembic_upgrade
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import setup_logging
from app.initial_data import seed
from app.routers import (
    auth,
    catalogo_productos,
    clientes,
    configuracion,
    dashboard,
    devoluciones,
    inconformidades,
    pqrs,
    seguimiento,
    usuarios,
)
from app.services.storage_service import ensure_upload_dirs


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Iniciando {settings.APP_NAME} en modo {settings.APP_ENV}")
    run_alembic_upgrade()
    Base.metadata.create_all(bind=engine)
    ensure_upload_dirs()
    try:
        seed()
    except Exception as e:
        logger.error(f"No se pudo aplicar seed inicial: {e}")
        raise
    yield
    logger.info("Apagando aplicación.")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API de gestión de PQRS (Peticiones, Quejas, Reclamos y Sugerencias). "
        "Autenticación JWT, control por roles, manejo de evidencias y dashboard."
    ),
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    logger.error(f"IntegrityError: {exc.orig}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Violación de integridad de datos.", "error": str(exc.orig)},
    )


@app.exception_handler(SQLAlchemyError)
async def sqla_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("SQLAlchemyError no manejado")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno de base de datos."},
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Datos inválidos.", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Error inesperado")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ha ocurrido un error inesperado."},
    )


api_prefix = "/api"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(usuarios.router, prefix=api_prefix)
app.include_router(clientes.router, prefix=api_prefix)
app.include_router(inconformidades.router, prefix=api_prefix)
app.include_router(catalogo_productos.router, prefix=api_prefix)
app.include_router(configuracion.router, prefix=api_prefix)
app.include_router(pqrs.router, prefix=api_prefix)
app.include_router(seguimiento.router, prefix=api_prefix)
app.include_router(devoluciones.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)


upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
