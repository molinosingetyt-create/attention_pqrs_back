"""Cliente: vendedor asignado y activo

Revision ID: 0002_cliente_vendedor_activo
Revises: 0001_initial
Create Date: 2026-04-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_cliente_vendedor_activo"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clientes",
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "clientes",
        sa.Column("vendedor_asignado_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_clientes_vendedor_asignado_id_usuarios",
        "clientes",
        "usuarios",
        ["vendedor_asignado_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_clientes_vendedor_asignado_id",
        "clientes",
        ["vendedor_asignado_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_clientes_vendedor_asignado_id", table_name="clientes")
    op.drop_constraint(
        "fk_clientes_vendedor_asignado_id_usuarios",
        "clientes",
        type_="foreignkey",
    )
    op.drop_column("clientes", "vendedor_asignado_id")
    op.drop_column("clientes", "activo")
