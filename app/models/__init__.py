"""Modelos ORM del sistema PQRS.

Importar aquí todos los modelos para que Alembic/SQLAlchemy los detecten
al momento de generar o crear el esquema.
"""
from app.models.area import Area  # noqa: F401
from app.models.categoria_producto import CategoriaProducto  # noqa: F401
from app.models.producto_catalogo import ProductoCatalogo  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.cliente import Cliente  # noqa: F401
from app.models.inconformidad import Inconformidad  # noqa: F401
from app.models.pqrs import PQRS  # noqa: F401
from app.models.producto_pqrs import ProductoPQRS  # noqa: F401
from app.models.evidencia import Evidencia  # noqa: F401
from app.models.seguimiento import Seguimiento  # noqa: F401
from app.models.devolucion import Devolucion  # noqa: F401
from app.models.rol_permiso import RolPermiso  # noqa: F401
