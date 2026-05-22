"""Agrega factura, lote y comentario por producto PQRS.

Revision ID: 0009_prod_pqrs_detalle
Revises: 0008_devolucion_codigo
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_prod_pqrs_detalle"
down_revision = "0008_devolucion_codigo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "productos_pqrs",
        sa.Column("numero_factura", sa.String(length=60), nullable=True),
    )
    op.add_column(
        "productos_pqrs",
        sa.Column("inconformidad_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "productos_pqrs",
        sa.Column("lote", sa.String(length=60), nullable=True),
    )
    op.add_column(
        "productos_pqrs",
        sa.Column("comentario", sa.String(length=1000), nullable=True),
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE productos_pqrs pp
            SET numero_factura = p.numero_factura,
                lote = p.lote,
                inconformidad_id = p.inconformidad_id
            FROM pqrs p
            WHERE pp.pqrs_id = p.id
              AND (pp.numero_factura IS NULL OR pp.lote IS NULL OR pp.inconformidad_id IS NULL)
            """
        )
    )
    op.create_foreign_key(
        "fk_productos_pqrs_inconformidad_id_inconformidades",
        "productos_pqrs",
        "inconformidades",
        ["inconformidad_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_productos_pqrs_inconformidad_id",
        "productos_pqrs",
        ["inconformidad_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_productos_pqrs_inconformidad_id", table_name="productos_pqrs")
    op.drop_constraint(
        "fk_productos_pqrs_inconformidad_id_inconformidades",
        "productos_pqrs",
        type_="foreignkey",
    )
    op.drop_column("productos_pqrs", "comentario")
    op.drop_column("productos_pqrs", "lote")
    op.drop_column("productos_pqrs", "inconformidad_id")
    op.drop_column("productos_pqrs", "numero_factura")
