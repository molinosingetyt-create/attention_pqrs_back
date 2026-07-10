"""Catálogo de permisos y matriz por defecto por rol.

La matriz efectiva se persiste en `rol_permisos` y puede actualizarse vía API
(`PUT /api/permisos/roles/{rol}`). Si un rol no tiene filas en BD, se usan
estos valores por defecto.
"""
from __future__ import annotations

from typing import TypedDict


class PermisoMeta(TypedDict):
    codigo: str
    modulo: str
    descripcion: str


class Permiso:
    DASHBOARD_VER = "dashboard.ver"

    CLIENTES_LISTAR = "clientes.listar"
    CLIENTES_CREAR = "clientes.crear"
    CLIENTES_EDITAR = "clientes.editar"
    CLIENTES_ELIMINAR = "clientes.eliminar"
    CLIENTES_ASIGNAR_VENDEDOR = "clientes.asignar_vendedor"
    CLIENTES_ACTIVAR = "clientes.activar_desactivar"
    CLIENTES_CARGA_MASIVA = "clientes.carga_masiva"

    PQRS_LISTAR = "pqrs.listar"
    PQRS_CREAR = "pqrs.crear"
    PQRS_VER = "pqrs.ver"
    PQRS_EDITAR = "pqrs.editar"
    PQRS_EXPORTAR = "pqrs.exportar"
    PQRS_SEGUIMIENTO_CREAR = "pqrs.seguimiento.crear"
    PQRS_EVIDENCIA_SUBIR = "pqrs.evidencia.subir"
    PQRS_FILTRAR_VENDEDOR = "pqrs.filtrar_vendedor"

    DEVOLUCIONES_LISTAR = "devoluciones.listar"
    DEVOLUCIONES_VALIDAR = "devoluciones.validar"

    USUARIOS_GESTIONAR = "usuarios.gestionar"
    USUARIOS_LISTAR_VENDEDORES = "usuarios.listar_vendedores"

    CONFIG_GESTIONAR = "configuracion.gestionar"
    INCONFORMIDADES_GESTIONAR = "inconformidades.gestionar"
    PERMISOS_GESTIONAR = "permisos.gestionar"


PERMISSION_CATALOG: list[PermisoMeta] = [
    {"codigo": Permiso.DASHBOARD_VER, "modulo": "dashboard", "descripcion": "Ver panel principal"},
    {"codigo": Permiso.CLIENTES_LISTAR, "modulo": "clientes", "descripcion": "Listar y buscar clientes"},
    {"codigo": Permiso.CLIENTES_CREAR, "modulo": "clientes", "descripcion": "Crear clientes"},
    {"codigo": Permiso.CLIENTES_EDITAR, "modulo": "clientes", "descripcion": "Editar datos de clientes"},
    {"codigo": Permiso.CLIENTES_ELIMINAR, "modulo": "clientes", "descripcion": "Eliminar clientes"},
    {"codigo": Permiso.CLIENTES_ASIGNAR_VENDEDOR, "modulo": "clientes", "descripcion": "Asignar o reasignar vendedor"},
    {"codigo": Permiso.CLIENTES_ACTIVAR, "modulo": "clientes", "descripcion": "Activar o desactivar clientes"},
    {"codigo": Permiso.CLIENTES_CARGA_MASIVA, "modulo": "clientes", "descripcion": "Cargue masivo de clientes"},
    {"codigo": Permiso.PQRS_LISTAR, "modulo": "pqrs", "descripcion": "Listar PQRS"},
    {"codigo": Permiso.PQRS_CREAR, "modulo": "pqrs", "descripcion": "Crear PQRS"},
    {"codigo": Permiso.PQRS_VER, "modulo": "pqrs", "descripcion": "Ver detalle de PQRS"},
    {"codigo": Permiso.PQRS_EDITAR, "modulo": "pqrs", "descripcion": "Editar PQRS"},
    {"codigo": Permiso.PQRS_EXPORTAR, "modulo": "pqrs", "descripcion": "Exportar PQRS a Excel"},
    {"codigo": Permiso.PQRS_SEGUIMIENTO_CREAR, "modulo": "pqrs", "descripcion": "Registrar seguimiento en historial"},
    {"codigo": Permiso.PQRS_EVIDENCIA_SUBIR, "modulo": "pqrs", "descripcion": "Subir evidencias a PQRS"},
    {"codigo": Permiso.PQRS_FILTRAR_VENDEDOR, "modulo": "pqrs", "descripcion": "Filtrar listado por vendedor"},
    {"codigo": Permiso.DEVOLUCIONES_LISTAR, "modulo": "devoluciones", "descripcion": "Ver devoluciones pendientes"},
    {"codigo": Permiso.DEVOLUCIONES_VALIDAR, "modulo": "devoluciones", "descripcion": "Registrar y validar devoluciones"},
    {"codigo": Permiso.USUARIOS_GESTIONAR, "modulo": "usuarios", "descripcion": "Gestionar usuarios del sistema"},
    {"codigo": Permiso.USUARIOS_LISTAR_VENDEDORES, "modulo": "usuarios", "descripcion": "Listar vendedores para asignación"},
    {"codigo": Permiso.CONFIG_GESTIONAR, "modulo": "configuracion", "descripcion": "Gestionar áreas, categorías y catálogo"},
    {"codigo": Permiso.INCONFORMIDADES_GESTIONAR, "modulo": "motivos", "descripcion": "Crear y editar motivos"},
    {"codigo": Permiso.PERMISOS_GESTIONAR, "modulo": "permisos", "descripcion": "Actualizar matriz de permisos por rol"},
]

ALL_PERMISSION_CODES: frozenset[str] = frozenset(p["codigo"] for p in PERMISSION_CATALOG)

_BASE_AUTHENTICATED = [
    Permiso.DASHBOARD_VER,
    Permiso.CLIENTES_LISTAR,
    Permiso.PQRS_LISTAR,
    Permiso.PQRS_VER,
    Permiso.PQRS_CREAR,
    Permiso.PQRS_EXPORTAR,
    Permiso.USUARIOS_LISTAR_VENDEDORES,
]

DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "ADMINISTRADOR": sorted(ALL_PERMISSION_CODES),
    "VENDEDOR": [
        *_BASE_AUTHENTICATED,
        Permiso.CLIENTES_CREAR,
        Permiso.CLIENTES_EDITAR,
    ],
    "ADMINISTRATIVO_COMERCIAL": [
        *_BASE_AUTHENTICATED,
        Permiso.CLIENTES_CREAR,
        Permiso.CLIENTES_EDITAR,
        Permiso.PQRS_EDITAR,
        Permiso.PQRS_SEGUIMIENTO_CREAR,
        Permiso.PQRS_EVIDENCIA_SUBIR,
        Permiso.PQRS_FILTRAR_VENDEDOR,
        Permiso.DEVOLUCIONES_LISTAR,
        Permiso.DEVOLUCIONES_VALIDAR,
    ],
    "CALIDAD": [
        *_BASE_AUTHENTICATED,
        Permiso.DEVOLUCIONES_LISTAR,
        Permiso.DEVOLUCIONES_VALIDAR,
        Permiso.INCONFORMIDADES_GESTIONAR,
    ],
}
