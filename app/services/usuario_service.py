from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import RolUsuario
from app.core.sede_scope import exigir_sede_activa, sede_id_alcance
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, _validar_sede_segun_rol


def _usuario_query():
    return select(Usuario).options(selectinload(Usuario.sede))


def list_usuarios(db: Session) -> list[Usuario]:
    return list(db.execute(_usuario_query().order_by(Usuario.id.desc())).scalars())


def list_vendedores(
    db: Session, solo_activos: bool = True, actor: Usuario | None = None
) -> list[Usuario]:
    """Usuarios con rol VENDEDOR (seleccionables para asignar PQRS)."""
    stmt = _usuario_query().where(Usuario.rol == RolUsuario.VENDEDOR.value)
    if solo_activos:
        stmt = stmt.where(Usuario.activo.is_(True))
    sid = sede_id_alcance(actor)
    if sid is not None:
        stmt = stmt.where(Usuario.sede_id == sid)
    stmt = stmt.order_by(Usuario.nombre.asc())
    return list(db.execute(stmt).scalars())


def get_usuario(db: Session, usuario_id: int) -> Usuario:
    user = db.execute(_usuario_query().where(Usuario.id == usuario_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return user


def _aplicar_sede(db: Session, rol: str, sede_id: int | None) -> int | None:
    rol_enum = RolUsuario(rol)
    resolved = _validar_sede_segun_rol(rol_enum, sede_id)
    if resolved is not None:
        exigir_sede_activa(db, resolved)
    return resolved


def create_usuario(db: Session, data: UsuarioCreate) -> Usuario:
    email = data.email.strip().lower()
    exists = db.execute(select(Usuario).where(Usuario.email == email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado.")
    sede_id = _aplicar_sede(db, data.rol.value, data.sede_id)
    user = Usuario(
        nombre=data.nombre.strip(),
        email=email,
        password_hash=hash_password(data.password),
        rol=data.rol.value,
        activo=data.activo,
        sede_id=sede_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return get_usuario(db, user.id)


def update_usuario(db: Session, usuario_id: int, data: UsuarioUpdate) -> Usuario:
    user = get_usuario(db, usuario_id)
    set_fields = data.model_fields_set

    if "nombre" in set_fields and data.nombre is not None:
        user.nombre = data.nombre.strip()
    if "rol" in set_fields and data.rol is not None:
        user.rol = data.rol.value
    if "activo" in set_fields and data.activo is not None:
        user.activo = data.activo
    if data.password:
        user.password_hash = hash_password(data.password)
    if "sede_id" in set_fields or "rol" in set_fields:
        nuevo_sede_id = data.sede_id if "sede_id" in set_fields else user.sede_id
        try:
            user.sede_id = _aplicar_sede(db, user.rol, nuevo_sede_id)
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    db.commit()
    return get_usuario(db, user.id)


def delete_usuario(db: Session, usuario_id: int) -> None:
    user = get_usuario(db, usuario_id)
    user.activo = False
    db.commit()
