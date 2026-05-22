from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


def list_usuarios(db: Session) -> list[Usuario]:
    return list(db.execute(select(Usuario).order_by(Usuario.id.desc())).scalars())


def list_vendedores(db: Session, solo_activos: bool = True) -> list[Usuario]:
    """Usuarios con rol VENDEDOR (seleccionables para asignar PQRS)."""
    stmt = select(Usuario).where(Usuario.rol == "VENDEDOR")
    if solo_activos:
        stmt = stmt.where(Usuario.activo.is_(True))
    stmt = stmt.order_by(Usuario.nombre.asc())
    return list(db.execute(stmt).scalars())


def get_usuario(db: Session, usuario_id: int) -> Usuario:
    user = db.get(Usuario, usuario_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return user


def create_usuario(db: Session, data: UsuarioCreate) -> Usuario:
    email = data.email.strip().lower()
    exists = db.execute(select(Usuario).where(Usuario.email == email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado.")
    user = Usuario(
        nombre=data.nombre.strip(),
        email=email,
        password_hash=hash_password(data.password),
        rol=data.rol.value,
        activo=data.activo,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_usuario(db: Session, usuario_id: int, data: UsuarioUpdate) -> Usuario:
    user = get_usuario(db, usuario_id)
    if data.nombre is not None:
        user.nombre = data.nombre.strip()
    if data.rol is not None:
        user.rol = data.rol.value
    if data.activo is not None:
        user.activo = data.activo
    if data.password:
        user.password_hash = hash_password(data.password)
    db.commit()
    db.refresh(user)
    return user


def delete_usuario(db: Session, usuario_id: int) -> None:
    user = get_usuario(db, usuario_id)
    user.activo = False
    db.commit()
