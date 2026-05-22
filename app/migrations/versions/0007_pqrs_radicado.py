"""Agrega radicado unico a PQRS

Revision ID: 0007_pqrs_radicado
Revises: 0006_devolucion_registro
Create Date: 2026-04-28 11:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_pqrs_radicado"
down_revision = "0006_devolucion_registro"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pqrs", sa.Column("radicado", sa.String(length=20), nullable=True))
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, tipo FROM pqrs WHERE radicado IS NULL")).mappings()
    suffix = {
        "PETICION": "P",
        "QUEJA": "Q",
        "RECLAMO": "R",
        "SUGERENCIA": "S",
        "OTRO": "O",
    }
    for row in rows:
        conn.execute(
            sa.text("UPDATE pqrs SET radicado = :radicado WHERE id = :id"),
            {
                "id": row["id"],
                "radicado": f"RAD-{row['id']:06d}{suffix.get(row['tipo'], 'O')}",
            },
        )
    op.create_index("ix_pqrs_radicado", "pqrs", ["radicado"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_pqrs_radicado", table_name="pqrs")
    op.drop_column("pqrs", "radicado")
