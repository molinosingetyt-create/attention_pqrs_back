from fastapi import HTTPException, status
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import RolUsuario
from app.core.permissions import Permiso
from app.services import permission_service
from app.models.cliente import Cliente
from app.models.pqrs import PQRS
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteCreate, ClienteUpdate


def _filtro_vendedor_lista(actor: Usuario | None):
    """Vendedor: clientes activos asignados a él o con al menos una PQRS suya."""
    if actor is None or actor.rol != RolUsuario.VENDEDOR.value:
        return None
    asignado = Cliente.vendedor_asignado_id == actor.id
    con_pqrs_propia = exists().where(
        and_(PQRS.cliente_id == Cliente.id, PQRS.vendedor_id == actor.id)
    )
    return and_(Cliente.activo.is_(True), or_(asignado, con_pqrs_propia))


def _vendedor_puede_ver_cliente(db: Session, cliente: Cliente, actor: Usuario) -> bool:
    if not cliente.activo:
        return False
    if cliente.vendedor_asignado_id == actor.id:
        return True
    row = db.execute(
        select(PQRS.id)
        .where(PQRS.cliente_id == cliente.id, PQRS.vendedor_id == actor.id)
        .limit(1)
    ).first()
    return row is not None


def list_clientes(
    db: Session,
    q: str | None = None,
    page: int = 1,
    size: int = 20,
    actor: Usuario | None = None,
) -> tuple[list[Cliente], int]:
    base = select(Cliente)
    scope = _filtro_vendedor_lista(actor)
    if scope is not None:
        base = base.where(scope)
    if q:
        like = f"%{q.strip().lower()}%"
        base = base.where(
            or_(
                func.lower(Cliente.nombre).like(like),
                func.lower(Cliente.apellidos).like(like),
                func.lower(Cliente.nit).like(like),
                func.lower(Cliente.correo).like(like),
            )
        )
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    rows = list(
        db.execute(
            base.order_by(Cliente.id.desc()).offset((page - 1) * size).limit(size)
        ).scalars()
    )
    return rows, int(total)


def get_cliente(db: Session, cliente_id: int, actor: Usuario | None = None) -> Cliente:
    c = db.get(Cliente, cliente_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")
    if actor is not None and actor.rol == RolUsuario.VENDEDOR.value:
        if not _vendedor_puede_ver_cliente(db, c, actor):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "No tienes permisos para ver este cliente.",
            )
    return c


def create_cliente(db: Session, data: ClienteCreate, actor: Usuario) -> Cliente:
    exists_cliente = db.execute(
        select(Cliente).where(Cliente.nit == data.nit.strip())
    ).scalar_one_or_none()
    if exists_cliente:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un cliente con ese NIT.")

    payload = data.model_dump(exclude={"vendedor_asignado_id"}, exclude_unset=False)
    vendedor_asignado_id: int | None = None

    if actor.rol == RolUsuario.VENDEDOR.value:
        vendedor_asignado_id = actor.id
    elif data.vendedor_asignado_id is not None:
        permission_service.exigir_permiso(db, actor, Permiso.CLIENTES_ASIGNAR_VENDEDOR)
        v = db.get(Usuario, data.vendedor_asignado_id)
        if not v or v.rol != RolUsuario.VENDEDOR.value or not v.activo:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "El vendedor asignado no existe o no es un vendedor activo.",
            )
        vendedor_asignado_id = data.vendedor_asignado_id

    cliente = Cliente(
        **payload,
        vendedor_asignado_id=vendedor_asignado_id,
        activo=True,
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def update_cliente(db: Session, cliente_id: int, data: ClienteUpdate, actor: Usuario) -> Cliente:
    cliente = get_cliente(db, cliente_id, actor=actor)
    changes = data.model_dump(exclude_unset=True)

    if actor.rol == RolUsuario.VENDEDOR.value:
        for forbidden in ("activo", "vendedor_asignado_id"):
            if forbidden in changes:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    "No puedes modificar el estado ni la asignación del cliente.",
                )
    elif actor.rol == RolUsuario.ADMINISTRATIVO_COMERCIAL.value:
        for forbidden in ("activo", "vendedor_asignado_id"):
            if forbidden in changes:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    "Solo el administrador puede deshabilitar clientes o asignar vendedor.",
                )

    if "vendedor_asignado_id" in changes:
        permission_service.exigir_permiso(db, actor, Permiso.CLIENTES_ASIGNAR_VENDEDOR)
    if "activo" in changes:
        permission_service.exigir_permiso(db, actor, Permiso.CLIENTES_ACTIVAR)

    if "vendedor_asignado_id" in changes:
        vid = changes["vendedor_asignado_id"]
        if vid is not None:
            v = db.get(Usuario, vid)
            if not v or v.rol != RolUsuario.VENDEDOR.value or not v.activo:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "El vendedor asignado no existe o no es un vendedor activo.",
                )

    for k, v in changes.items():
        setattr(cliente, k, v)
    db.commit()
    db.refresh(cliente)
    return cliente


def delete_cliente(db: Session, cliente_id: int) -> None:
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")
    db.delete(cliente)
    db.commit()
