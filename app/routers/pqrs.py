from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.enums import EstadoPQRS, RolUsuario, TipoPQRS
from app.models.usuario import Usuario
from app.schemas.common import Page
from app.schemas.pqrs import (
    EvidenciaOut,
    PQRSCreate,
    PQRSDetail,
    PQRSListItem,
    PQRSUpdate,
    ProductoPQRSCreate,
    ProductoPQRSOut,
    SeguimientoOut,
)
from app.services import pqrs_service, storage_service


router = APIRouter(
    prefix="/pqrs",
    tags=["PQRS"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/",
    response_model=PQRSDetail,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles(
                RolUsuario.ADMINISTRADOR,
                RolUsuario.ADMINISTRATIVO_COMERCIAL,
                RolUsuario.VENDEDOR,
                RolUsuario.CALIDAD,
            )
        )
    ],
)
def crear_pqrs(
    data: PQRSCreate,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    pqrs = pqrs_service.create_pqrs(db, data, actor)
    return _to_detail(pqrs)


@router.get("/", response_model=Page[PQRSListItem])
def listar_pqrs(
    estado: EstadoPQRS | None = Query(None),
    tipo: TipoPQRS | None = Query(None),
    cliente_id: int | None = Query(None),
    vendedor_id: int | None = Query(None),
    q: str | None = Query(None),
    fecha_desde: datetime | None = Query(None),
    fecha_hasta: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    items, total = pqrs_service.list_pqrs(
        db,
        estado=estado,
        tipo=tipo,
        cliente_id=cliente_id,
        vendedor_id=vendedor_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        q=q,
        page=page,
        size=size,
        actor=actor,
    )
    return Page(
        items=[PQRSListItem.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/export")
def exportar_pqrs(
    estado: EstadoPQRS | None = Query(None),
    tipo: TipoPQRS | None = Query(None),
    cliente_id: int | None = Query(None),
    vendedor_id: int | None = Query(None),
    q: str | None = Query(None),
    fecha_desde: datetime | None = Query(None),
    fecha_hasta: datetime | None = Query(None),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    """Exporta PQRS filtradas a Excel (.xlsx)."""
    from openpyxl import Workbook

    items, _ = pqrs_service.list_pqrs(
        db,
        estado=estado,
        tipo=tipo,
        cliente_id=cliente_id,
        vendedor_id=vendedor_id,
        q=q,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        page=1,
        size=10_000,
        actor=actor,
    )
    wb = Workbook()
    ws = wb.active
    ws.title = "PQRS"
    ws.append(
        [
            "Radicado",
            "Tipo",
            "Estado",
            "Cliente",
            "Vendedor",
            "Área responsable",
            "Factura",
            "Fecha creación",
            "Fecha cierre",
        ]
    )
    for it in items:
        ws.append(
            [
                it["radicado"],
                it["tipo"],
                it["estado"],
                it["cliente_nombre"],
                it["vendedor_nombre"],
                it["area_nombre"] or "",
                it["numero_factura"] or "",
                it["fecha_creacion"].strftime("%Y-%m-%d %H:%M") if it["fecha_creacion"] else "",
                it["fecha_cierre"].strftime("%Y-%m-%d %H:%M") if it["fecha_cierre"] else "",
            ]
        )
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=pqrs.xlsx"},
    )


@router.get("/{pqrs_id}", response_model=PQRSDetail)
def detalle(
    pqrs_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    return _to_detail(pqrs_service.get_pqrs_detail(db, pqrs_id, actor=actor))


@router.put(
    "/{pqrs_id}",
    response_model=PQRSDetail,
    dependencies=[
        Depends(
            require_roles(
                RolUsuario.ADMINISTRADOR,
                RolUsuario.ADMINISTRATIVO_COMERCIAL,
            )
        )
    ],
)
def actualizar(
    pqrs_id: int,
    data: PQRSUpdate,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    return _to_detail(pqrs_service.update_pqrs(db, pqrs_id, data, actor))


@router.post("/{pqrs_id}/productos", response_model=list[ProductoPQRSOut])
def agregar_productos(
    pqrs_id: int,
    productos: list[ProductoPQRSCreate],
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    creados = pqrs_service.add_productos(db, pqrs_id, productos, actor=actor)
    return [ProductoPQRSOut.model_validate(p) for p in creados]


@router.delete("/{pqrs_id}/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(
    pqrs_id: int,
    producto_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    pqrs_service.delete_producto(db, pqrs_id, producto_id, actor=actor)


@router.post("/{pqrs_id}/evidencias", response_model=EvidenciaOut)
async def subir_evidencia(
    pqrs_id: int,
    file: UploadFile = File(...),
    carga_inicial: bool = Query(False),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    stored = await storage_service.save_upload(file, folder=f"pqrs/{pqrs_id}")
    ev = pqrs_service.add_evidencia(
        db,
        pqrs_id=pqrs_id,
        archivo_url=stored.url,
        nombre_original=stored.original_name,
        content_type=stored.content_type,
        actor=actor,
        carga_inicial=carga_inicial,
    )
    return EvidenciaOut.model_validate(ev)


@router.post("/{pqrs_id}/notificar-calidad")
def notificar_calidad_pqrs(
    pqrs_id: int,
    db: Session = Depends(get_db),
):
    pqrs_service.notify_calidad_for_pqrs(db, pqrs_id)
    return {"ok": True}


@router.get("/{pqrs_id}/seguimientos", response_model=list[SeguimientoOut])
def seguimientos(pqrs_id: int, db: Session = Depends(get_db)):
    segs = pqrs_service.listar_seguimientos(db, pqrs_id)
    return [_seg_to_out(s) for s in segs]


def _seg_to_out(seg) -> SeguimientoOut:
    return SeguimientoOut(
        id=seg.id,
        estado=seg.estado,
        descripcion=seg.descripcion,
        usuario_id=seg.usuario_id,
        usuario_nombre=seg.usuario.nombre if seg.usuario else None,
        fecha=seg.fecha,
    )


def _to_detail(pqrs) -> PQRSDetail:
    from app.schemas.cliente import ClienteOut
    from app.schemas.inconformidad import InconformidadOut
    from app.schemas.pqrs import (
        EvidenciaOut,
        ProductoPQRSOut,
        UsuarioMini,
    )

    return PQRSDetail(
        id=pqrs.id,
        radicado=pqrs.radicado or pqrs_service._generar_radicado(pqrs.id, pqrs.tipo),
        tipo=pqrs.tipo,
        estado=pqrs.estado,
        numero_factura=pqrs.numero_factura,
        lote=pqrs.lote,
        descripcion=pqrs.descripcion,
        fecha_creacion=pqrs.fecha_creacion,
        fecha_cierre=pqrs.fecha_cierre,
        cliente=ClienteOut.model_validate(pqrs.cliente),
        inconformidad=InconformidadOut.model_validate(pqrs.inconformidad) if pqrs.inconformidad else None,
        vendedor=UsuarioMini.model_validate(pqrs.vendedor) if pqrs.vendedor else None,
        productos=[ProductoPQRSOut.model_validate(p) for p in pqrs.productos],
        evidencias=[EvidenciaOut.model_validate(e) for e in pqrs.evidencias],
        seguimientos=[_seg_to_out(s) for s in pqrs.seguimientos],
    )
