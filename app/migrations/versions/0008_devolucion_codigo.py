"""Agrega codigo consecutivo a devoluciones radicadas

Revision ID: 0008_devolucion_codigo
Revises: 0007_pqrs_radicado
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_devolucion_codigo"
down_revision = "0007_pqrs_radicado"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "devoluciones",
        sa.Column("codigo_devolucion", sa.String(length=20), nullable=True),
    )

    conn = op.get_bind()
    rows = (
        conn.execute(
            sa.text(
                """
                SELECT id
                FROM devoluciones
                WHERE pendiente = false
                ORDER BY fecha_decision ASC, id ASC
                """
            )
        )
        .mappings()
        .all()
    )
    for idx, row in enumerate(rows, start=1):
        conn.execute(
            sa.text(
                """
                UPDATE devoluciones
                SET codigo_devolucion = :codigo
                WHERE id = :id
                """
            ),
            {"codigo": f"DEV-{idx:06d}", "id": row["id"]},
        )

    op.create_index(
        "ix_devoluciones_codigo_devolucion",
        "devoluciones",
        ["codigo_devolucion"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_devoluciones_codigo_devolucion", table_name="devoluciones")
    op.drop_column("devoluciones", "codigo_devolucion")
