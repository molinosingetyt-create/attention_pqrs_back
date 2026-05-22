from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.enums import RolUsuario
from app.schemas.inconformidad import (
    InconformidadCreate,
    InconformidadOut,
    InconformidadUpdate,
)
from app.services import inconformidad_service


router = APIRouter(
    prefix="/inconformidades",
    tags=["Inconformidades"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[InconformidadOut])
def listar(solo_activos: bool = True, db: Session = Depends(get_db)):
    return inconformidad_service.list_inconformidades(db, solo_activos=solo_activos)


@router.post(
    "/",
    response_model=InconformidadOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RolUsuario.ADMINISTRADOR))],
)
def crear(data: InconformidadCreate, db: Session = Depends(get_db)):
    return inconformidad_service.create_inconformidad(db, data)


@router.put(
    "/{inc_id}",
    response_model=InconformidadOut,
    dependencies=[Depends(require_roles(RolUsuario.ADMINISTRADOR))],
)
def actualizar(inc_id: int, data: InconformidadUpdate, db: Session = Depends(get_db)):
    return inconformidad_service.update_inconformidad(db, inc_id, data)


@router.delete(
    "/{inc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RolUsuario.ADMINISTRADOR))],
)
def eliminar(inc_id: int, db: Session = Depends(get_db)):
    inconformidad_service.delete_inconformidad(db, inc_id)
