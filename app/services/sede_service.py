from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.sede import Sede
from app.models.usuario import Usuario
from app.schemas.sede import SedeCreate, SedeUpdate


def list_sedes(db: Session, *, solo_activas: bool = False) -> list[Sede]:
    stmt = select(Sede)
    if solo_activas:
        stmt = stmt.where(Sede.activa.is_(True))
    return list(db.execute(stmt.order_by(Sede.nombre.asc())).scalars())


def get_sede(db: Session, sede_id: int) -> Sede:
    sede = db.get(Sede, sede_id)
    if not sede:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sede no encontrada")
    return sede


def create_sede(db: Session, data: SedeCreate) -> Sede:
    codigo = data.codigo.strip().upper()
    if db.execute(select(Sede.id).where(Sede.codigo == codigo)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una sede con ese código.")
    sede = Sede(codigo=codigo, nombre=data.nombre.strip(), activa=data.activa)
    db.add(sede)
    db.commit()
    db.refresh(sede)
    return sede


def update_sede(db: Session, sede_id: int, data: SedeUpdate) -> Sede:
    sede = get_sede(db, sede_id)
    ch = data.model_dump(exclude_unset=True)
    if "codigo" in ch and ch["codigo"] is not None:
        codigo = ch["codigo"].strip().upper()
        exists = db.execute(
            select(Sede.id).where(Sede.codigo == codigo, Sede.id != sede_id)
        ).first()
        if exists:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una sede con ese código.")
        sede.codigo = codigo
    if "nombre" in ch and ch["nombre"] is not None:
        sede.nombre = ch["nombre"].strip()
    if "activa" in ch and ch["activa"] is not None:
        sede.activa = ch["activa"]
    db.commit()
    db.refresh(sede)
    return sede


def delete_sede(db: Session, sede_id: int) -> None:
    sede = get_sede(db, sede_id)
    n_u = db.execute(
        select(func.count()).select_from(Usuario).where(Usuario.sede_id == sede_id)
    ).scalar_one()
    n_c = db.execute(
        select(func.count()).select_from(Cliente).where(Cliente.sede_id == sede_id)
    ).scalar_one()
    if int(n_u) > 0 or int(n_c) > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede eliminar: hay usuarios o clientes asociados a esta sede.",
        )
    db.delete(sede)
    db.commit()
