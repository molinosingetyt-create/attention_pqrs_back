"""Satisfacción del cliente por PQRS.

Revision ID: 0014_pqrs_satisfaccion
Revises: 0013_pqrs_analisis
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014_pqrs_satisfaccion"
down_revision = "0013_pqrs_analisis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pqrs_satisfaccion_cliente",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pqrs_id", sa.Integer(), nullable=False),
        sa.Column("atencion_oportunidad", sa.String(length=20), nullable=False),
        sa.Column("expectativa_cumplida", sa.Boolean(), nullable=False),
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
        sa.UniqueConstraint("pqrs_id", name="uq_pqrs_satisfaccion_cliente_pqrs_id"),
    )
    op.create_index(
        "ix_pqrs_satisfaccion_cliente_pqrs_id",
        "pqrs_satisfaccion_cliente",
        ["pqrs_id"],
    )
    op.create_index(
        "ix_pqrs_satisfaccion_cliente_usuario_id",
        "pqrs_satisfaccion_cliente",
        ["usuario_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pqrs_satisfaccion_cliente_usuario_id",
        table_name="pqrs_satisfaccion_cliente",
    )
    op.drop_index(
        "ix_pqrs_satisfaccion_cliente_pqrs_id",
        table_name="pqrs_satisfaccion_cliente",
    )
    op.drop_table("pqrs_satisfaccion_cliente")
