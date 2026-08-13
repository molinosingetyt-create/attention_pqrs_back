"""Comentarios opcionales en satisfacción del cliente.

Revision ID: 0015_satisfaccion_comentarios
Revises: 0014_pqrs_satisfaccion
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015_satisfaccion_comentarios"
down_revision = "0014_pqrs_satisfaccion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pqrs_satisfaccion_cliente",
        sa.Column("comentarios", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pqrs_satisfaccion_cliente", "comentarios")
