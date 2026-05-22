"""Esquema inicial PQRS

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("email", sa.String(180), nullable=False, unique=True),
        sa.Column("contrasena", sa.String(255), nullable=False),
        sa.Column("rol", sa.String(40), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)
    op.create_index("ix_usuarios_rol", "usuarios", ["rol"])

    op.create_table(
        "clientes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("apellidos", sa.String(120), nullable=True),
        sa.Column("nit", sa.String(40), nullable=False, unique=True),
        sa.Column("direccion", sa.String(200), nullable=True),
        sa.Column("telefono", sa.String(40), nullable=True),
        sa.Column("correo", sa.String(180), nullable=True),
        sa.Column("ciudad", sa.String(100), nullable=True),
    )
    op.create_index("ix_clientes_nit", "clientes", ["nit"], unique=True)
    op.create_index("ix_clientes_nombre", "clientes", ["nombre"])
    op.create_index("ix_clientes_correo", "clientes", ["correo"])

    op.create_table(
        "inconformidades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(150), nullable=False, unique=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_inconformidades_nombre", "inconformidades", ["nombre"], unique=True)

    op.create_table(
        "pqrs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "cliente_id",
            sa.Integer(),
            sa.ForeignKey("clientes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vendedor_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "inconformidad_id",
            sa.Integer(),
            sa.ForeignKey("inconformidades.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ABIERTA"),
        sa.Column("numero_factura", sa.String(60), nullable=True),
        sa.Column("lote", sa.String(60), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("fecha_cierre", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pqrs_cliente_id", "pqrs", ["cliente_id"])
    op.create_index("ix_pqrs_vendedor_id", "pqrs", ["vendedor_id"])
    op.create_index("ix_pqrs_inconformidad_id", "pqrs", ["inconformidad_id"])
    op.create_index("ix_pqrs_tipo", "pqrs", ["tipo"])
    op.create_index("ix_pqrs_estado", "pqrs", ["estado"])
    op.create_index("ix_pqrs_fecha_creacion", "pqrs", ["fecha_creacion"])
    op.create_index("ix_pqrs_numero_factura", "pqrs", ["numero_factura"])

    op.create_table(
        "productos_pqrs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "pqrs_id",
            sa.Integer(),
            sa.ForeignKey("pqrs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nombre_producto", sa.String(180), nullable=False),
        sa.Column("cantidad", sa.Numeric(12, 2), nullable=False, server_default="1"),
    )
    op.create_index("ix_productos_pqrs_pqrs_id", "productos_pqrs", ["pqrs_id"])

    op.create_table(
        "evidencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "pqrs_id",
            sa.Integer(),
            sa.ForeignKey("pqrs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("archivo_url", sa.String(500), nullable=False),
        sa.Column("nombre_original", sa.String(255), nullable=True),
        sa.Column("content_type", sa.String(120), nullable=True),
        sa.Column(
            "fecha_subida",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_evidencias_pqrs_id", "evidencias", ["pqrs_id"])

    op.create_table(
        "seguimientos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "pqrs_id",
            sa.Integer(),
            sa.ForeignKey("pqrs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_seguimientos_pqrs_id", "seguimientos", ["pqrs_id"])
    op.create_index("ix_seguimientos_usuario_id", "seguimientos", ["usuario_id"])

    op.create_table(
        "devoluciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "pqrs_id",
            sa.Integer(),
            sa.ForeignKey("pqrs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("aplica", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column(
            "fecha_decision",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_devoluciones_pqrs_id", "devoluciones", ["pqrs_id"], unique=True)


def downgrade() -> None:
    op.drop_table("devoluciones")
    op.drop_table("seguimientos")
    op.drop_table("evidencias")
    op.drop_table("productos_pqrs")
    op.drop_table("pqrs")
    op.drop_table("inconformidades")
    op.drop_table("clientes")
    op.drop_table("usuarios")
