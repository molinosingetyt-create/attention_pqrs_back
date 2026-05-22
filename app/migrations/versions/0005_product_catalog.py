"""Catálogo de productos por categoría y FK opcional en productos_pqrs.

Revision ID: 0005_prod_catalog
Revises: 0004_contam_fis_bio
Create Date: 2026-04-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision: str = "0005_prod_catalog"
down_revision: Union[str, None] = "0004_contam_fis_bio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)

    if not insp.has_table("categorias_producto"):
        op.create_table(
            "categorias_producto",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("nombre", sa.String(150), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        )
        op.create_index("ix_categorias_producto_nombre", "categorias_producto", ["nombre"], unique=True)

    insp = inspect(conn)
    if not insp.has_table("productos_catalogo"):
        op.create_table(
            "productos_catalogo",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("categoria_id", sa.Integer(), nullable=False),
            sa.Column("nombre", sa.String(250), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        )
        op.create_foreign_key(
            "fk_productos_catalogo_categoria",
            "productos_catalogo",
            "categorias_producto",
            ["categoria_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index("ix_productos_catalogo_categoria_id", "productos_catalogo", ["categoria_id"])
        op.create_unique_constraint(
            "uq_producto_catalogo_cat_nombre",
            "productos_catalogo",
            ["categoria_id", "nombre"],
        )

    insp = inspect(conn)
    if not _has_column(insp, "productos_pqrs", "producto_catalogo_id"):
        op.add_column(
            "productos_pqrs",
            sa.Column("producto_catalogo_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_productos_pqrs_producto_catalogo",
            "productos_pqrs",
            "productos_catalogo",
            ["producto_catalogo_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            "ix_productos_pqrs_producto_catalogo_id",
            "productos_pqrs",
            ["producto_catalogo_id"],
        )

    op.alter_column(
        "productos_pqrs",
        "nombre_producto",
        existing_type=sa.String(180),
        type_=sa.String(250),
        existing_nullable=False,
    )

    from app.data.catalogo_productos import CATEGORIAS_CON_PRODUCTOS

    for orden_cat, (cat_nombre, productos) in enumerate(CATEGORIAS_CON_PRODUCTOS):
        conn.execute(
            text(
                "INSERT INTO categorias_producto (nombre, activo, orden) "
                "SELECT :n, true, :o WHERE NOT EXISTS (SELECT 1 FROM categorias_producto c WHERE c.nombre = :n)"
            ),
            {"n": cat_nombre, "o": orden_cat},
        )
        cid = conn.execute(
            text("SELECT id FROM categorias_producto WHERE nombre = :n"),
            {"n": cat_nombre},
        ).scalar()
        if not cid:
            continue
        for orden_p, nom_p in enumerate(productos):
            conn.execute(
                text(
                    "INSERT INTO productos_catalogo (categoria_id, nombre, activo, orden) "
                    "SELECT :cid, :nom, true, :ord "
                    "WHERE NOT EXISTS (SELECT 1 FROM productos_catalogo p "
                    "WHERE p.categoria_id = :cid AND p.nombre = :nom)"
                ),
                {"cid": cid, "nom": nom_p, "ord": orden_p},
            )


def _has_column(insp, table: str, column: str) -> bool:
    if not insp.has_table(table):
        return False
    return any(c["name"] == column for c in insp.get_columns(table))


def downgrade() -> None:
    op.drop_constraint("fk_productos_pqrs_producto_catalogo", "productos_pqrs", type_="foreignkey")
    op.drop_index("ix_productos_pqrs_producto_catalogo_id", table_name="productos_pqrs")
    op.drop_column("productos_pqrs", "producto_catalogo_id")
    op.alter_column(
        "productos_pqrs",
        "nombre_producto",
        existing_type=sa.String(250),
        type_=sa.String(180),
        existing_nullable=False,
    )
    op.drop_table("productos_catalogo")
    op.drop_table("categorias_producto")
