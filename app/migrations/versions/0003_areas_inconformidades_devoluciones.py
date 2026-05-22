"""Áreas, inconformidades por área, pendiente en devoluciones

Revision ID: 0003_areas_inc_dev (≤32 chars: columna alembic_version en init_db.sql)

Revises: 0002_cliente_vendedor_activo
Create Date: 2026-04-23

Idempotente: si un intento anterior dejó tablas/columnas creadas pero no actualizó
alembic_version, upgrade puede repetirse sin error.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision: str = "0003_areas_inc_dev"
down_revision: Union[str, None] = "0002_cliente_vendedor_activo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _drop_nombre_unique(bind):
    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text(
                "ALTER TABLE inconformidades DROP CONSTRAINT IF EXISTS inconformidades_nombre_key"
            )
        )
    else:
        try:
            op.drop_index("ix_inconformidades_nombre", table_name="inconformidades")
        except Exception:
            pass


def _has_table(insp, name: str) -> bool:
    return name in insp.get_table_names()


def _has_column(insp, table: str, column: str) -> bool:
    if not _has_table(insp, table):
        return False
    return any(c["name"] == column for c in insp.get_columns(table))


def _has_index(insp, table: str, index_name: str) -> bool:
    if not _has_table(insp, table):
        return False
    return any(i["name"] == index_name for i in insp.get_indexes(table))


def _pg_constraint_exists(conn, name: str) -> bool:
    r = conn.execute(
        text("SELECT 1 FROM pg_constraint WHERE conname = :n"),
        {"n": name},
    ).scalar()
    return r is not None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)

    # --- areas ---
    if not _has_table(insp, "areas"):
        op.create_table(
            "areas",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("codigo", sa.String(40), nullable=False),
            sa.Column("nombre", sa.String(120), nullable=False),
        )
        op.create_index("ix_areas_codigo", "areas", ["codigo"], unique=True)
    elif not _has_index(insp, "areas", "ix_areas_codigo"):
        op.create_index("ix_areas_codigo", "areas", ["codigo"], unique=True)

    for row in (
        (1, "CALIDAD", "CALIDAD"),
        (2, "LOGISTICA", "LOGISTICA"),
        (3, "COMERCIAL", "COMERCIAL"),
    ):
        conn.execute(
            text(
                "INSERT INTO areas (id, codigo, nombre) SELECT :id, :codigo, :nombre "
                "WHERE NOT EXISTS (SELECT 1 FROM areas a WHERE a.codigo = :codigo)"
            ),
            {"id": row[0], "codigo": row[1], "nombre": row[2]},
        )

    insp = inspect(conn)

    # --- inconformidades: area_id, descripcion ---
    if not _has_column(insp, "inconformidades", "area_id"):
        op.add_column("inconformidades", sa.Column("area_id", sa.Integer(), nullable=True))
    if not _has_column(insp, "inconformidades", "descripcion"):
        op.add_column("inconformidades", sa.Column("descripcion", sa.Text(), nullable=True))

    calidad_id = conn.execute(text("SELECT id FROM areas WHERE codigo = 'CALIDAD' LIMIT 1")).scalar()
    if calidad_id is not None:
        conn.execute(
            text("UPDATE inconformidades SET area_id = :aid WHERE area_id IS NULL"),
            {"aid": calidad_id},
        )

    if not _pg_constraint_exists(conn, "fk_inconformidades_area_id_areas"):
        op.create_foreign_key(
            "fk_inconformidades_area_id_areas",
            "inconformidades",
            "areas",
            ["area_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    op.alter_column("inconformidades", "area_id", nullable=False)

    _drop_nombre_unique(conn)

    insp = inspect(conn)
    if not _has_index(insp, "inconformidades", "ix_inconformidades_area_id"):
        op.create_index("ix_inconformidades_area_id", "inconformidades", ["area_id"])

    if not _pg_constraint_exists(conn, "uq_inconformidad_area_nombre"):
        op.create_unique_constraint(
            "uq_inconformidad_area_nombre", "inconformidades", ["area_id", "nombre"]
        )

    insp = inspect(conn)
    if not _has_column(insp, "devoluciones", "pendiente"):
        op.add_column(
            "devoluciones",
            sa.Column(
                "pendiente",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

    catalog = [
        (1, "CALIDAD EMPAQUE", "Empaque, sellado y presentación del producto."),
        (1, "CALIDAD DE PRODUCTO", "Características físicas o organolépticas del producto."),
        (1, "CONTAMINACIÓN FÍSICA", "Cuerpos extraños, materiales o partículas de origen físico."),
        (1, "CONTAMINACIÓN BIOLÓGICA", "Microorganismos, mohos u otros contaminantes de origen biológico."),
        (1, "MAL COLOR", "Color del producto no conforme."),
        (1, "MAL OLOR", "Olor del producto no conforme."),
        (1, "MAL SABOR", "Sabor del producto no conforme."),
        (1, "ROTULADO BOLSA", "Etiquetado o rotulación en bolsa."),
        (1, "CONTENIDO NETO", "Peso o volumen neto declarado."),
        (2, "TIEMPO DE ENTREGA", "Demoras o incumplimiento en plazos de entrega."),
        (2, "PRODUCTO NO ENTREGADO", "Faltantes o no entrega del pedido."),
        (2, "MAL TRATO PERSONAL", "Trato inadecuado por parte del personal."),
        (3, "MAL ATENCIÓN", "Atención comercial o postventa deficiente."),
    ]
    ins = text(
        """
        INSERT INTO inconformidades (area_id, nombre, descripcion, activo)
        SELECT :area_id, :nombre, :desc, true
        WHERE NOT EXISTS (
          SELECT 1 FROM inconformidades i
          WHERE i.area_id = :area_id AND i.nombre = :nombre
        )
        """
    )
    for area_id, nombre, desc in catalog:
        conn.execute(ins, {"area_id": area_id, "nombre": nombre, "desc": desc})


def downgrade() -> None:
    op.drop_constraint("uq_inconformidad_area_nombre", "inconformidades", type_="unique")
    op.drop_index("ix_inconformidades_area_id", table_name="inconformidades")
    op.drop_constraint("fk_inconformidades_area_id_areas", "inconformidades", type_="foreignkey")
    op.drop_column("inconformidades", "descripcion")
    op.drop_column("inconformidades", "area_id")
    op.drop_column("devoluciones", "pendiente")
    op.drop_index("ix_areas_codigo", table_name="areas")
    op.drop_table("areas")
    op.create_index("ix_inconformidades_nombre", "inconformidades", ["nombre"], unique=True)
