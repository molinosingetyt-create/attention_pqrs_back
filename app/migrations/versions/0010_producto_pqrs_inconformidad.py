"""Agrega inconformidad por producto PQRS.

Revision ID: 0010_prod_pqrs_inc
Revises: 0009_prod_pqrs_detalle
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_prod_pqrs_inc"
down_revision = "0009_prod_pqrs_detalle"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def _has_fk(table_name: str, fk_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(fk["name"] == fk_name for fk in inspector.get_foreign_keys(table_name))


def upgrade() -> None:
    if not _has_column("productos_pqrs", "inconformidad_id"):
        op.add_column(
            "productos_pqrs",
            sa.Column("inconformidad_id", sa.Integer(), nullable=True),
        )

    if not _has_fk("productos_pqrs", "fk_productos_pqrs_inconformidad_id_inconformidades"):
        op.create_foreign_key(
            "fk_productos_pqrs_inconformidad_id_inconformidades",
            "productos_pqrs",
            "inconformidades",
            ["inconformidad_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not _has_index("productos_pqrs", "ix_productos_pqrs_inconformidad_id"):
        op.create_index(
            "ix_productos_pqrs_inconformidad_id",
            "productos_pqrs",
            ["inconformidad_id"],
        )

    op.execute(
        """
        UPDATE productos_pqrs pp
        SET inconformidad_id = p.inconformidad_id
        FROM pqrs p
        WHERE pp.pqrs_id = p.id
          AND pp.inconformidad_id IS NULL
          AND p.inconformidad_id IS NOT NULL
        """
    )


def downgrade() -> None:
    if _has_index("productos_pqrs", "ix_productos_pqrs_inconformidad_id"):
        op.drop_index("ix_productos_pqrs_inconformidad_id", table_name="productos_pqrs")
    if _has_fk("productos_pqrs", "fk_productos_pqrs_inconformidad_id_inconformidades"):
        op.drop_constraint(
            "fk_productos_pqrs_inconformidad_id_inconformidades",
            "productos_pqrs",
            type_="foreignkey",
        )
    if _has_column("productos_pqrs", "inconformidad_id"):
        op.drop_column("productos_pqrs", "inconformidad_id")
