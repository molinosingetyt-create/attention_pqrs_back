from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.enums import EstadoPQRS, TipoEvidencia, TipoPQRS
from app.core.permissions import Permiso
from app.models.usuario import Usuario
from app.schemas.common import Page
from app.schemas.pqrs import (
    AnalisisResponsabilidadOut,
    AnalisisResponsabilidadUpsert,
    EvidenciaOut,
    PQRSCreate,
    PQRSDetail,
    PQRSListItem,
    PQRSUpdate,
    ProductoPQRSCreate,
    ProductoPQRSOut,
    SatisfaccionClienteOut,
    SatisfaccionClienteUpsert,
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
    dependencies=[Depends(require_permission(Permiso.PQRS_CREAR))],
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
            "Estado área resp.",
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
                it["estado_area_responsable"],
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
    dependencies=[Depends(require_permission(Permiso.PQRS_EDITAR))],
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
    _: None = Depends(require_permission(Permiso.PQRS_EDITAR)),
):
    creados = pqrs_service.add_productos(db, pqrs_id, productos, actor=actor)
    return [ProductoPQRSOut.model_validate(p) for p in creados]


@router.delete("/{pqrs_id}/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(
    pqrs_id: int,
    producto_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
    _: None = Depends(require_permission(Permiso.PQRS_EDITAR)),
):
    pqrs_service.delete_producto(db, pqrs_id, producto_id, actor=actor)


@router.post("/{pqrs_id}/evidencias", response_model=EvidenciaOut)
async def subir_evidencia(
    pqrs_id: int,
    file: UploadFile = File(...),
    producto_pqrs_id: int = Query(...),
    tipo: TipoEvidencia = Query(...),
    carga_inicial: bool = Query(False),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    stored = await storage_service.save_upload(
        file, folder=f"pqrs/{pqrs_id}/productos/{producto_pqrs_id}"
    )
    ev = pqrs_service.add_evidencia(
        db,
        pqrs_id=pqrs_id,
        archivo_url=stored.url,
        nombre_original=stored.original_name,
        content_type=stored.content_type,
        producto_pqrs_id=producto_pqrs_id,
        tipo=tipo,
        actor=actor,
        carga_inicial=carga_inicial,
    )
    return EvidenciaOut.model_validate(ev)


@router.put("/{pqrs_id}/analisis-responsabilidad", response_model=AnalisisResponsabilidadOut)
def guardar_analisis_responsabilidad(
    pqrs_id: int,
    data: AnalisisResponsabilidadUpsert,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    analisis = pqrs_service.upsert_analisis_responsabilidad(db, pqrs_id, data, actor)
    return _analisis_to_out(analisis)


@router.put("/{pqrs_id}/satisfaccion-cliente", response_model=SatisfaccionClienteOut)
def guardar_satisfaccion_cliente(
    pqrs_id: int,
    data: SatisfaccionClienteUpsert,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    registro = pqrs_service.upsert_satisfaccion_cliente(db, pqrs_id, data, actor)
    return _satisfaccion_to_out(registro)


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


def _satisfaccion_to_out(registro) -> SatisfaccionClienteOut:
    return SatisfaccionClienteOut(
        id=registro.id,
        atencion_oportunidad=registro.atencion_oportunidad,
        expectativa_cumplida=registro.expectativa_cumplida,
        usuario_id=registro.usuario_id,
        usuario_nombre=registro.usuario.nombre if registro.usuario else None,
        fecha_actualizacion=registro.fecha_actualizacion,
    )


def _analisis_to_out(analisis) -> AnalisisResponsabilidadOut:
    return AnalisisResponsabilidadOut(
        id=analisis.id,
        procedente=analisis.procedente,
        comentario=analisis.comentario,
        usuario_id=analisis.usuario_id,
        usuario_nombre=analisis.usuario.nombre if analisis.usuario else None,
        fecha_actualizacion=analisis.fecha_actualizacion,
    )


def _to_detail(pqrs) -> PQRSDetail:
    from app.schemas.cliente import ClienteOut
    from app.schemas.inconformidad import InconformidadOut
    from app.schemas.pqrs import (
        EvidenciaOut,
        ProductoPQRSOut,
        UsuarioMini,
    )

    productos_out = []
    for p in pqrs.productos:
        prod = ProductoPQRSOut.model_validate(p)
        prod.evidencias = [
            EvidenciaOut.model_validate(e)
            for e in sorted(
                p.evidencias,
                key=lambda x: (x.tipo or "", x.fecha_subida),
            )
        ]
        productos_out.append(prod)

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
        productos=productos_out,
        evidencias=[EvidenciaOut.model_validate(e) for e in pqrs.evidencias],
        seguimientos=[_seg_to_out(s) for s in pqrs.seguimientos],
        analisis_responsabilidad=(
            _analisis_to_out(pqrs.analisis_responsabilidad)
            if pqrs.analisis_responsabilidad
            else None
        ),
        satisfaccion_cliente=(
            _satisfaccion_to_out(pqrs.satisfaccion_cliente)
            if pqrs.satisfaccion_cliente
            else None
        ),
    )
