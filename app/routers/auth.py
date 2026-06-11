from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Permiso
from app.core.security import create_access_token
from app.models.usuario import Usuario
from app.schemas.auth import SessionOut, TokenResponse
from app.services import permission_service
from app.schemas.usuario import UsuarioCreate, UsuarioOut
from app.services import auth_service, usuario_service


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login con email (en campo `username`) y contraseña. Retorna JWT."""
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        subject=user.id, extra_claims={"rol": user.rol, "email": user.email}
    )
    permisos = permission_service.permisos_usuario(db, user)
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UsuarioOut.model_validate(user),
        permisos=permisos,
    )


@router.post(
    "/register",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permiso.USUARIOS_GESTIONAR))],
)
def register(data: UsuarioCreate, db: Session = Depends(get_db)):
    """Registro de usuario: solo accesible para administradores."""
    return usuario_service.create_usuario(db, data)


@router.get("/me", response_model=SessionOut)
def me(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return SessionOut(
        user=UsuarioOut.model_validate(current),
        permisos=permission_service.permisos_usuario(db, current),
    )
