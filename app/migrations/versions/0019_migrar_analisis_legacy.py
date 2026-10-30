"""Copia el análisis por radicado (legacy) a cada producto de la PQRS.

Las PQRS conceptuadas antes de 0018 solo tienen fila en
`pqrs_analisis_responsabilidad`: el listado las muestra como procedente/no
procedente (fallback), pero el detalle solo lee `producto_pqrs_analisis` y
aparece sin concepto. Se replica el concepto legacy en cada producto, solo para
PQRS que aún no tienen ningún concepto por producto (misma regla del fallback).

Revision ID: 0019_migrar_analisis_legacy
Revises: 0018_analisis_producto
"""

from __future__ import annotations

from alembic import op

revision = "0019_migrar_analisis_legacy"
down_revision = "0018_analisis_producto"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO producto_pqrs_analisis
            (producto_pqrs_id, procedente, comentario, usuario_id, fecha_actualizacion)
        SELECT p.id, l.procedente, l.comentario, l.usuario_id, l.fecha_actualizacion
        FROM pqrs_analisis_responsabilidad l
        JOIN productos_pqrs p ON p.pqrs_id = l.pqrs_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM productos_pqrs p2
            JOIN producto_pqrs_analisis a ON a.producto_pqrs_id = p2.id
            WHERE p2.pqrs_id = l.pqrs_id
        )
        """
    )


def downgrade() -> None:
    # No se revierte: las filas copiadas no se distinguen de conceptos posteriores
    # y la tabla legacy se conserva intacta.
    pass
