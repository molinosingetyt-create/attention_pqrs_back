"""Atención/oportunidad opcional en satisfacción del cliente.

Revision ID: 0016_sat_atencion_opt
Revises: 0015_satisfaccion_comentarios
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016_sat_atencion_opt"
down_revision = "0015_satisfaccion_comentarios"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "pqrs_satisfaccion_cliente",
        "atencion_oportunidad",
        existing_type=sa.String(length=20),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(
        "UPDATE pqrs_satisfaccion_cliente "
        "SET atencion_oportunidad = 'BUENA' "
        "WHERE atencion_oportunidad IS NULL"
    )
    op.alter_column(
        "pqrs_satisfaccion_cliente",
        "atencion_oportunidad",
        existing_type=sa.String(length=20),
        nullable=False,
    )
