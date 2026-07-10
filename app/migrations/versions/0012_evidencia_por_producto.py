"""Evidencias asociadas a producto y tipo de foto.

Revision ID: 0012_evidencia_producto
Revises: 0011_rol_permisos
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_evidencia_producto"
down_revision = "0011_rol_permisos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evidencias",
        sa.Column("producto_pqrs_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "evidencias",
        sa.Column("tipo", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "evidencias",
        sa.Column("titulo", sa.String(length=150), nullable=True),
    )
    op.create_foreign_key(
        "fk_evidencias_producto_pqrs",
        "evidencias",
        "productos_pqrs",
        ["producto_pqrs_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_evidencias_producto_pqrs_id",
        "evidencias",
        ["producto_pqrs_id"],
    )
    op.create_unique_constraint(
        "uq_evidencia_producto_tipo",
        "evidencias",
        ["producto_pqrs_id", "tipo"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_evidencia_producto_tipo", "evidencias", type_="unique")
    op.drop_index("ix_evidencias_producto_pqrs_id", table_name="evidencias")
    op.drop_constraint("fk_evidencias_producto_pqrs", "evidencias", type_="foreignkey")
    op.drop_column("evidencias", "titulo")
    op.drop_column("evidencias", "tipo")
    op.drop_column("evidencias", "producto_pqrs_id")
