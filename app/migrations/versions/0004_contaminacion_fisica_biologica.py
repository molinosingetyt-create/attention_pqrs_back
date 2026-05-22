"""Sustituye inconformidad única CONTAMINACIÓN por FÍSICA y BIOLÓGICA.

Revision ID: 0004_contam_fis_bio
Revises: 0003_areas_inc_dev
Create Date: 2026-04-23

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0004_contam_fis_bio"
down_revision: Union[str, None] = "0003_areas_inc_dev"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    calidad_id = conn.execute(
        text("SELECT id FROM areas WHERE codigo = 'CALIDAD' LIMIT 1")
    ).scalar()
    if not calidad_id:
        return

    nuevas = (
        (
            "CONTAMINACIÓN FÍSICA",
            "Cuerpos extraños, materiales o partículas de origen físico.",
        ),
        (
            "CONTAMINACIÓN BIOLÓGICA",
            "Microorganismos, mohos u otros contaminantes de origen biológico.",
        ),
    )
    ins = text(
        """
        INSERT INTO inconformidades (area_id, nombre, descripcion, activo)
        SELECT :aid, :nom, :d, true
        WHERE NOT EXISTS (
          SELECT 1 FROM inconformidades i
          WHERE i.area_id = :aid AND i.nombre = :nom
        )
        """
    )
    for nom, desc in nuevas:
        conn.execute(ins, {"aid": calidad_id, "nom": nom, "d": desc})

    legacy_id = conn.execute(
        text(
            "SELECT id FROM inconformidades "
            "WHERE area_id = :aid AND nombre = 'CONTAMINACIÓN' LIMIT 1"
        ),
        {"aid": calidad_id},
    ).scalar()
    if legacy_id:
        conn.execute(
            text("UPDATE pqrs SET inconformidad_id = NULL WHERE inconformidad_id = :id"),
            {"id": legacy_id},
        )
        conn.execute(text("DELETE FROM inconformidades WHERE id = :id"), {"id": legacy_id})


def downgrade() -> None:
    pass
