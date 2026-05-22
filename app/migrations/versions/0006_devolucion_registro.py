"""Campos de registro de devolución (fecha generación + JSON de radicado)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_devolucion_registro"
down_revision = "0005_prod_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "devoluciones",
        sa.Column("fecha_registro", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE devoluciones SET fecha_registro = fecha_decision WHERE fecha_registro IS NULL"
    )
    op.alter_column(
        "devoluciones",
        "fecha_registro",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.add_column(
        "devoluciones",
        sa.Column("datos_registro", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("devoluciones", "datos_registro")
    op.drop_column("devoluciones", "fecha_registro")
