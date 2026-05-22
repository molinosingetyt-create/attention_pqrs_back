from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import EstadoPQRS, RolUsuario
from app.models.area import Area
from app.models.cliente import Cliente
from app.models.inconformidad import Inconformidad
from app.models.pqrs import PQRS
from app.models.usuario import Usuario


def _radicado_pqrs(pqrs: PQRS) -> str:
    suffix = {
        "PETICION": "P",
        "QUEJA": "Q",
        "RECLAMO": "R",
        "SUGERENCIA": "S",
        "OTRO": "O",
    }.get(pqrs.tipo, "O")
    return pqrs.radicado or f"RAD-{pqrs.id:06d}{suffix}"


def _aplicar_scope_vendedor(stmt, actor: Usuario | None):
    """Si el actor es VENDEDOR, limita el query a sus propias PQRS."""
    if actor is not None and actor.rol == RolUsuario.VENDEDOR.value:
        return stmt.where(PQRS.vendedor_id == actor.id)
    return stmt


def _month_start(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(dt: datetime, months: int) -> datetime:
    # dt assumed to be month-start
    y = dt.year + (dt.month - 1 + months) // 12
    m = (dt.month - 1 + months) % 12 + 1
    return dt.replace(year=y, month=m)


def get_dashboard(db: Session, actor: Usuario | None = None) -> dict:
    estados_stmt = _aplicar_scope_vendedor(
        select(PQRS.estado, func.count(PQRS.id)).group_by(PQRS.estado), actor
    )
    estados = dict(db.execute(estados_stmt).all())

    tipos_stmt = _aplicar_scope_vendedor(
        select(PQRS.tipo, func.count(PQRS.id)).group_by(PQRS.tipo), actor
    )
    tipos = db.execute(tipos_stmt).all()

    areas_stmt = _aplicar_scope_vendedor(
        select(
            func.coalesce(Area.codigo, "SIN_AREA").label("area_codigo"),
            func.coalesce(Area.nombre, "Sin área").label("area_nombre"),
            func.count(PQRS.id).label("cantidad"),
        )
        .select_from(PQRS)
        .join(Inconformidad, Inconformidad.id == PQRS.inconformidad_id, isouter=True)
        .join(Area, Area.id == Inconformidad.area_id, isouter=True)
        .group_by("area_codigo", "area_nombre")
        .order_by(func.count(PQRS.id).desc()),
        actor,
    )
    areas = db.execute(areas_stmt).all()

    now = datetime.now(tz=timezone.utc)
    last_month = _month_start(now)
    first_month = _add_months(last_month, -11)

    por_mes_stmt = _aplicar_scope_vendedor(
        select(
            func.date_trunc("month", PQRS.fecha_creacion).label("mes"),
            func.count(PQRS.id).label("cantidad"),
        )
        .where(PQRS.fecha_creacion >= first_month)
        .group_by("mes")
        .order_by("mes"),
        actor,
    )
    por_mes_rows = db.execute(por_mes_stmt).all()
    por_mes_map = {r[0].strftime("%Y-%m"): int(r[1]) for r in por_mes_rows if r[0]}
    meses = []
    cursor = first_month
    for _ in range(12):
        key = cursor.strftime("%Y-%m")
        meses.append({"mes": key, "cantidad": int(por_mes_map.get(key, 0))})
        cursor = _add_months(cursor, 1)

    total = sum(estados.values())
    abiertas = estados.get(EstadoPQRS.ABIERTA.value, 0)
    en_proceso = estados.get(EstadoPQRS.EN_PROCESO.value, 0)
    cerradas = estados.get(EstadoPQRS.CERRADA.value, 0)
    rechazadas = estados.get(EstadoPQRS.RECHAZADA.value, 0)

    recientes_stmt = _aplicar_scope_vendedor(
        select(PQRS, Cliente.nombre)
        .join(Cliente, Cliente.id == PQRS.cliente_id)
        .order_by(PQRS.fecha_creacion.desc())
        .limit(5),
        actor,
    )
    recientes_rows = db.execute(recientes_stmt).all()

    recientes = [
        {
            "id": r[0].id,
            "radicado": _radicado_pqrs(r[0]),
            "tipo": r[0].tipo,
            "estado": r[0].estado,
            "cliente": r[1],
            "fecha_creacion": r[0].fecha_creacion,
        }
        for r in recientes_rows
    ]

    return {
        "kpis": {
            "total": int(total),
            "abiertas": int(abiertas),
            "en_proceso": int(en_proceso),
            "cerradas": int(cerradas),
            "rechazadas": int(rechazadas),
        },
        "por_tipo": [{"tipo": t, "cantidad": int(c)} for t, c in tipos],
        "por_estado": [{"tipo": e, "cantidad": int(c)} for e, c in estados.items()],
        "por_area": [
            {"area_codigo": a, "area_nombre": n, "cantidad": int(c)} for a, n, c in areas
        ],
        "por_mes": meses,
        "recientes": recientes,
    }
