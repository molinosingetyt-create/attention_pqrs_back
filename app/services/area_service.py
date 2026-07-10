from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.area import Area
from app.models.inconformidad import Inconformidad
from app.schemas.area import AreaCreate, AreaUpdate


def list_areas(db: Session) -> list[Area]:
    return list(db.execute(select(Area).order_by(Area.codigo.asc())).scalars())


def create_area(db: Session, data: AreaCreate) -> Area:
    codigo = data.codigo.strip().upper()
    if db.execute(select(Area.id).where(Area.codigo == codigo)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un área con ese código.")
    a = Area(codigo=codigo, nombre=data.nombre.strip())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def update_area(db: Session, area_id: int, data: AreaUpdate) -> Area:
    a = db.get(Area, area_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Área no encontrada")
    ch = data.model_dump(exclude_unset=True)
    if "codigo" in ch and ch["codigo"] is not None:
        codigo = ch["codigo"].strip().upper()
        exists = db.execute(
            select(Area.id).where(Area.codigo == codigo, Area.id != area_id)
        ).first()
        if exists:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un área con ese código.")
        a.codigo = codigo
    if "nombre" in ch and ch["nombre"] is not None:
        a.nombre = ch["nombre"].strip()
    db.commit()
    db.refresh(a)
    return a


def delete_area(db: Session, area_id: int) -> None:
    a = db.get(Area, area_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Área no encontrada")
    n = db.execute(
        select(func.count()).select_from(Inconformidad).where(Inconformidad.area_id == area_id)
    ).scalar_one()
    if int(n) > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede eliminar: hay motivos asociados a esta área.",
        )
    db.delete(a)
    db.commit()
