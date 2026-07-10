from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.area import Area
from app.models.inconformidad import Inconformidad
from app.schemas.inconformidad import InconformidadCreate, InconformidadUpdate


def list_inconformidades(db: Session, solo_activos: bool = True) -> list[Inconformidad]:
    stmt = (
        select(Inconformidad)
        .options(selectinload(Inconformidad.area))
        .join(Inconformidad.area)
        .order_by(Area.nombre.asc(), Inconformidad.nombre.asc())
    )
    if solo_activos:
        stmt = stmt.where(Inconformidad.activo.is_(True))
    return list(db.execute(stmt).scalars())


def create_inconformidad(db: Session, data: InconformidadCreate) -> Inconformidad:
    area = db.get(Area, data.area_id)
    if not area:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El área no existe.")
    exists = db.execute(
        select(Inconformidad).where(
            Inconformidad.area_id == data.area_id,
            Inconformidad.nombre == data.nombre.strip(),
        )
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ya existe un motivo con ese nombre en el mismo área.",
        )
    inc = Inconformidad(
        area_id=data.area_id,
        nombre=data.nombre.strip(),
        descripcion=data.descripcion.strip() if data.descripcion else None,
        activo=data.activo,
    )
    db.add(inc)
    db.commit()
    return db.execute(
        select(Inconformidad)
        .where(Inconformidad.id == inc.id)
        .options(selectinload(Inconformidad.area))
    ).scalar_one()


def update_inconformidad(db: Session, inc_id: int, data: InconformidadUpdate) -> Inconformidad:
    inc = db.execute(
        select(Inconformidad)
        .where(Inconformidad.id == inc_id)
        .options(selectinload(Inconformidad.area))
    ).scalar_one_or_none()
    if not inc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Motivo no encontrado")
    changes = data.model_dump(exclude_unset=True)
    if "area_id" in changes and changes["area_id"] is not None:
        area = db.get(Area, changes["area_id"])
        if not area:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El área no existe.")
        inc.area_id = changes["area_id"]
    if "nombre" in changes and changes["nombre"] is not None:
        inc.nombre = changes["nombre"].strip()
    if "descripcion" in changes:
        raw = changes["descripcion"]
        inc.descripcion = raw.strip() if raw else None
    if "activo" in changes and changes["activo"] is not None:
        inc.activo = changes["activo"]
    db.commit()
    return db.execute(
        select(Inconformidad)
        .where(Inconformidad.id == inc.id)
        .options(selectinload(Inconformidad.area))
    ).scalar_one()


def delete_inconformidad(db: Session, inc_id: int) -> None:
    inc = db.execute(
        select(Inconformidad).where(Inconformidad.id == inc_id)
    ).scalar_one_or_none()
    if not inc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Motivo no encontrado")
    db.delete(inc)
    db.commit()
