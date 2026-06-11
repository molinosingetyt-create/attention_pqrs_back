"""Dependencias FastAPI compartidas: usuario actual y autorización por roles."""
from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import RolUsuario
from app.core.security import decode_token
from app.models.usuario import Usuario
from app.services import permission_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except ValueError:
        raise credentials_exc

    user = db.get(Usuario, int(user_id))
    if not user or not user.activo:
        raise credentials_exc
    return user


def require_roles(*roles: RolUsuario):
    """Factory de dependencia que valida que el usuario actual tenga alguno de los roles."""

    allowed: Iterable[str] = {r.value if isinstance(r, RolUsuario) else r for r in roles}

    def _checker(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.rol not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción.",
            )
        return user

    return _checker


def require_permission(*permisos: str):
    """Factory: exige al menos uno de los permisos indicados."""

    def _checker(
        user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Usuario:
        permission_service.exigir_permiso(db, user, *permisos)
        return user

    return _checker
