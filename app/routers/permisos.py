from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.enums import RolUsuario
from app.core.permissions import Permiso
from app.models.usuario import Usuario
from app.schemas.permisos import (
    MatrizPermisosOut,
    PermisoCatalogoOut,
    RolPermisosOut,
    RolPermisosUpdate,
)
from app.services import permission_service

_admin_only = [Depends(require_roles(RolUsuario.ADMINISTRADOR))]

router = APIRouter(prefix="/permisos", tags=["Permisos"])


@router.get(
    "/catalogo",
    response_model=list[PermisoCatalogoOut],
    dependencies=_admin_only,
)
def listar_catalogo():
    """Catálogo de permisos (solo administrador)."""
    return [PermisoCatalogoOut(**p) for p in permission_service.catalogo()]


@router.get("/mis-permisos", response_model=list[str])
def mis_permisos(
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    """Permisos efectivos del usuario autenticado (para el frontend)."""
    return permission_service.permisos_usuario(db, actor)


@router.get(
    "/matriz",
    response_model=MatrizPermisosOut,
    dependencies=_admin_only,
)
def matriz_permisos(db: Session = Depends(get_db)):
    """Matriz completa rol → permisos (solo administrador)."""
    data = permission_service.matriz_completa(db)
    return MatrizPermisosOut(
        roles=[RolPermisosOut(rol=rol, permisos=perms) for rol, perms in data.items()]
    )


@router.put(
    "/roles/{rol}",
    response_model=RolPermisosOut,
    dependencies=_admin_only,
)
def actualizar_permisos_rol(
    rol: str,
    body: RolPermisosUpdate,
    db: Session = Depends(get_db),
):
    """Reemplaza los permisos de un rol (solo administrador)."""
    perms = permission_service.actualizar_rol(db, rol, body.permisos)
    return RolPermisosOut(rol=rol, permisos=perms)
