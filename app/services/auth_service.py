"""Servicio de autenticación."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.usuario import Usuario


def authenticate_user(db: Session, email: str, password: str) -> Usuario | None:
    email = email.strip().lower()
    user = db.execute(select(Usuario).where(Usuario.email == email)).scalar_one_or_none()
    if not user or not user.activo:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
