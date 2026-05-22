"""Ejecuta migraciones Alembic al arrancar la API (Docker y local)."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from loguru import logger
from sqlalchemy import inspect

from app.core.config import settings
from app.core.database import engine


def run_alembic_upgrade() -> None:
    """
    Aplica `alembic upgrade head`.

    Si la base ya tiene tablas (p. ej. creadas con scripts/init_db.sql) pero no
    existe `alembic_version`, se hace `stamp` en 0001_initial para alinear el
    historial y poder aplicar 0002, 0003, etc. sin fallar al crear tablas duplicadas.
    """
    # Raíz del proyecto backend (donde está alembic.ini en la imagen Docker)
    root = Path(__file__).resolve().parents[2]
    ini_path = root / "alembic.ini"
    if not ini_path.is_file():
        logger.warning("No se encontró alembic.ini en {}; se omiten migraciones.", root)
        return

    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "alembic_version" not in tables and "usuarios" in tables:
        logger.info(
            "Base con tablas previas sin Alembic (p. ej. init_db.sql); "
            "stamp en revisión 0001_initial."
        )
        command.stamp(cfg, "0001_initial")

    logger.info("Alembic: upgrade head")
    command.upgrade(cfg, "head")
    logger.info("Alembic: migraciones al día.")
