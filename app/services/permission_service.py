from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.enums import RolUsuario
from app.core.permissions import (
    ALL_PERMISSION_CODES,
    DEFAULT_ROLE_PERMISSIONS,
    PERMISSION_CATALOG,
    Permiso,
    PermisoMeta,
)
from app.models.rol_permiso import RolPermiso
from app.models.usuario import Usuario

_ROLES_VALIDOS = {r.value for r in RolUsuario}


def _validate_codes(codes: list[str]) -> list[str]:
    invalid = sorted({c for c in codes if c not in ALL_PERMISSION_CODES})
    if invalid:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Permisos no reconocidos: {', '.join(invalid)}",
        )
    return sorted(set(codes))


def catalogo() -> list[PermisoMeta]:
    return list(PERMISSION_CATALOG)


def permisos_de_rol_en_db(db: Session, rol: str) -> list[str] | None:
    rows = list(
        db.execute(
            select(RolPermiso.permiso)
            .where(RolPermiso.rol == rol)
            .order_by(RolPermiso.permiso.asc())
        ).scalars()
    )
    return rows if rows else None


def permisos_efectivos_rol(db: Session, rol: str) -> list[str]:
    custom = permisos_de_rol_en_db(db, rol)
    if custom is not None:
        return custom
    return list(DEFAULT_ROLE_PERMISSIONS.get(rol, []))


def permisos_usuario(db: Session, user: Usuario) -> list[str]:
    return permisos_efectivos_rol(db, user.rol)


def usuario_tiene(db: Session, user: Usuario, *permisos: str) -> bool:
    if not permisos:
        return True
    asignados = set(permisos_efectivos_rol(db, user.rol))
    return any(p in asignados for p in permisos)


def usuario_tiene_todos(db: Session, user: Usuario, *permisos: str) -> bool:
    if not permisos:
        return True
    asignados = set(permisos_efectivos_rol(db, user.rol))
    return all(p in asignados for p in permisos)


def exigir_permiso(db: Session, user: Usuario, *permisos: str) -> None:
    if not usuario_tiene(db, user, *permisos):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "No tienes permisos para realizar esta acción.",
        )


def matriz_completa(db: Session) -> dict[str, list[str]]:
    return {rol: permisos_efectivos_rol(db, rol) for rol in sorted(_ROLES_VALIDOS)}


def actualizar_rol(db: Session, rol: str, permisos: list[str]) -> list[str]:
    if rol not in _ROLES_VALIDOS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Rol no válido: {rol}")
    codes = _validate_codes(permisos)
    if rol != RolUsuario.ADMINISTRADOR.value:
        codes = [c for c in codes if c != Permiso.PERMISOS_GESTIONAR]
    if rol == RolUsuario.ADMINISTRADOR.value and Permiso.PERMISOS_GESTIONAR not in codes:
        codes.append(Permiso.PERMISOS_GESTIONAR)
        codes.sort()
    db.execute(delete(RolPermiso).where(RolPermiso.rol == rol))
    for code in codes:
        db.add(RolPermiso(rol=rol, permiso=code))
    db.commit()
    return codes


def sembrar_defaults(db: Session) -> None:
    """Inserta la matriz por defecto solo si la tabla está vacía."""
    exists = db.execute(select(RolPermiso.rol).limit(1)).scalar_one_or_none()
    if exists:
        return
    for rol, perms in DEFAULT_ROLE_PERMISSIONS.items():
        for code in perms:
            db.add(RolPermiso(rol=rol, permiso=code))
    db.commit()
