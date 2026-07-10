"""Análisis y asignación de responsabilidad por PQRS.

Revision ID: 0013_pqrs_analisis
Revises: 0012_evidencia_producto
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013_pqrs_analisis"
down_revision = "0012_evidencia_producto"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pqrs_analisis_responsabilidad",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pqrs_id", sa.Integer(), nullable=False),
        sa.Column("procedente", sa.Boolean(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["pqrs_id"], ["pqrs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pqrs_id", name="uq_pqrs_analisis_responsabilidad_pqrs_id"),
    )
    op.create_index(
        "ix_pqrs_analisis_responsabilidad_pqrs_id",
        "pqrs_analisis_responsabilidad",
        ["pqrs_id"],
    )
    op.create_index(
        "ix_pqrs_analisis_responsabilidad_usuario_id",
        "pqrs_analisis_responsabilidad",
        ["usuario_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pqrs_analisis_responsabilidad_usuario_id",
        table_name="pqrs_analisis_responsabilidad",
    )
    op.drop_index(
        "ix_pqrs_analisis_responsabilidad_pqrs_id",
        table_name="pqrs_analisis_responsabilidad",
    )
    op.drop_table("pqrs_analisis_responsabilidad")
