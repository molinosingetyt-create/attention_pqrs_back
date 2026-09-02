"""Sedes y asociación de usuarios/clientes.

Revision ID: 0017_sedes
Revises: 0016_sat_atencion_opt
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0017_sedes"
down_revision = "0016_sat_atencion_opt"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sedes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_sedes_codigo", "sedes", ["codigo"], unique=True)

    op.add_column("usuarios", sa.Column("sede_id", sa.Integer(), nullable=True))
    op.create_index("ix_usuarios_sede_id", "usuarios", ["sede_id"])
    op.create_foreign_key(
        "fk_usuarios_sede_id",
        "usuarios",
        "sedes",
        ["sede_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("clientes", sa.Column("sede_id", sa.Integer(), nullable=True))
    op.create_index("ix_clientes_sede_id", "clientes", ["sede_id"])
    op.create_foreign_key(
        "fk_clientes_sede_id",
        "clientes",
        "sedes",
        ["sede_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_clientes_sede_id", "clientes", type_="foreignkey")
    op.drop_index("ix_clientes_sede_id", table_name="clientes")
    op.drop_column("clientes", "sede_id")

    op.drop_constraint("fk_usuarios_sede_id", "usuarios", type_="foreignkey")
    op.drop_index("ix_usuarios_sede_id", table_name="usuarios")
    op.drop_column("usuarios", "sede_id")

    op.drop_index("ix_sedes_codigo", table_name="sedes")
    op.drop_table("sedes")
