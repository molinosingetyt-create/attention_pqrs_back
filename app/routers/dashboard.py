from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.usuario import Usuario
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    fecha_inicio: datetime | None = Query(None),
    fecha_fin: datetime | None = Query(None),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    return dashboard_service.get_dashboard(
        db,
        actor,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
