from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Permiso
from app.schemas.sede import SedeCreate, SedeOut, SedeUpdate
from app.services import sede_service

router = APIRouter(
    prefix="/sedes",
    tags=["Sedes"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[SedeOut])
def listar(
    solo_activas: bool = Query(False),
    db: Session = Depends(get_db),
):
    return sede_service.list_sedes(db, solo_activas=solo_activas)


@router.post(
    "/",
    response_model=SedeOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permiso.SEDES_GESTIONAR))],
)
def crear(data: SedeCreate, db: Session = Depends(get_db)):
    return sede_service.create_sede(db, data)


@router.put(
    "/{sede_id}",
    response_model=SedeOut,
    dependencies=[Depends(require_permission(Permiso.SEDES_GESTIONAR))],
)
def actualizar(sede_id: int, data: SedeUpdate, db: Session = Depends(get_db)):
    return sede_service.update_sede(db, sede_id, data)


@router.delete(
    "/{sede_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permiso.SEDES_GESTIONAR))],
)
def eliminar(sede_id: int, db: Session = Depends(get_db)):
    sede_service.delete_sede(db, sede_id)
