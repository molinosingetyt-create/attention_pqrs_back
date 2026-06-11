from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.enums import RolUsuario
from app.core.permissions import Permiso
from app.models.usuario import Usuario
from app.schemas.devolucion import (
    DevolucionDetalleOut,
    DevolucionPendienteOut,
    DevolucionRegistroIn,
)
from app.services import devolucion_service

router = APIRouter(
    prefix="/devoluciones",
    tags=["Devoluciones"],
    dependencies=[
        Depends(get_current_user),
        Depends(require_permission(Permiso.DEVOLUCIONES_LISTAR)),
    ],
)


def _assert_calidad_area(actor: Usuario, area_codigo: str) -> None:
    if actor.rol == RolUsuario.CALIDAD.value and area_codigo != "CALIDAD":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "No tienes permisos para gestionar devoluciones fuera del área CALIDAD.",
        )


@router.get("/", response_model=list[DevolucionPendienteOut])
def listar_pendientes(
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    """PQRS con inconformidad: pendientes de radicar y devoluciones ya radicadas."""
    return devolucion_service.list_devoluciones_pendientes(db, actor)


@router.get("/{devolucion_id}", response_model=DevolucionDetalleOut)
def obtener_detalle(
    devolucion_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    row = devolucion_service.get_devolucion_detalle(db, devolucion_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Devolución no encontrada")
    _assert_calidad_area(actor, row["area_codigo"])
    return DevolucionDetalleOut.model_validate(row)


@router.put("/{devolucion_id}/registro", response_model=DevolucionDetalleOut)
def guardar_radicado(
    devolucion_id: int,
    data: DevolucionRegistroIn,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    prev = devolucion_service.get_devolucion_detalle(db, devolucion_id)
    if not prev:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Devolución no encontrada")
    _assert_calidad_area(actor, prev["area_codigo"])
    try:
        devolucion_service.guardar_registro_radico(
            db, devolucion_id, data, usuario_id=actor.id
        )
        db.commit()
    except ValueError as e:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    row = devolucion_service.get_devolucion_detalle(db, devolucion_id)
    assert row is not None
    return DevolucionDetalleOut.model_validate(row)
