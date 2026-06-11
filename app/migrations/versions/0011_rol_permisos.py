"""Tabla rol_permisos para matriz de permisos editable.

Revision ID: 0011_rol_permisos
Revises: 0010_prod_pqrs_inc
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_rol_permisos"
down_revision = "0010_prod_pqrs_inc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rol_permisos",
        sa.Column("rol", sa.String(length=40), nullable=False),
        sa.Column("permiso", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("rol", "permiso"),
    )


def downgrade() -> None:
    op.drop_table("rol_permisos")
