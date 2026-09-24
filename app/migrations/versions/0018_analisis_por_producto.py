"""Concepto de responsabilidad por producto de la PQRS.

El análisis deja de ser uno por radicado y pasa a uno por producto, para que un
mismo radicado pueda quedar procedente en un producto y no procedente en otro.
La tabla `pqrs_analisis_responsabilidad` se conserva como histórico de lectura.

Revision ID: 0018_analisis_producto
Revises: 0017_sedes
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0018_analisis_producto"
down_revision = "0017_sedes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "producto_pqrs_analisis",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("producto_pqrs_id", sa.Integer(), nullable=False),
        sa.Column("procedente", sa.Boolean(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["producto_pqrs_id"], ["productos_pqrs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "producto_pqrs_id", name="uq_producto_pqrs_analisis_producto_pqrs_id"
        ),
    )
    op.create_index(
        "ix_producto_pqrs_analisis_producto_pqrs_id",
        "producto_pqrs_analisis",
        ["producto_pqrs_id"],
    )
    op.create_index(
        "ix_producto_pqrs_analisis_usuario_id",
        "producto_pqrs_analisis",
        ["usuario_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_producto_pqrs_analisis_usuario_id", table_name="producto_pqrs_analisis"
    )
    op.drop_index(
        "ix_producto_pqrs_analisis_producto_pqrs_id", table_name="producto_pqrs_analisis"
    )
    op.drop_table("producto_pqrs_analisis")
