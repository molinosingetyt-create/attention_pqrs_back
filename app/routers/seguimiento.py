from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Permiso
from app.models.usuario import Usuario
from app.schemas.pqrs import SeguimientoCreate, SeguimientoOut
from app.services import pqrs_service


router = APIRouter(prefix="/seguimientos", tags=["Seguimientos"])


@router.post(
    "/pqrs/{pqrs_id}",
    response_model=SeguimientoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permiso.PQRS_SEGUIMIENTO_CREAR))],
)
def crear(
    pqrs_id: int,
    data: SeguimientoCreate,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    seg = pqrs_service.add_seguimiento(
        db, pqrs_id=pqrs_id, estado=data.estado, descripcion=data.descripcion, actor=actor
    )
    return SeguimientoOut(
        id=seg.id,
        estado=seg.estado,
        descripcion=seg.descripcion,
        usuario_id=seg.usuario_id,
        usuario_nombre=actor.nombre,
        fecha=seg.fecha,
    )
