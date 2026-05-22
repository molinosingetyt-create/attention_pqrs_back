"""Servicio principal de PQRS."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import EstadoPQRS, RolUsuario, TipoPQRS
from app.core.config import settings
from app.models.cliente import Cliente
from app.models.evidencia import Evidencia
from app.models.inconformidad import Inconformidad
from app.models.pqrs import PQRS
from app.models.producto_catalogo import ProductoCatalogo
from app.models.producto_pqrs import ProductoPQRS
from app.models.seguimiento import Seguimiento
from app.models.usuario import Usuario
from app.schemas.pqrs import PQRSCreate, PQRSUpdate, ProductoPQRSCreate
from app.services import devolucion_service, email_service


_RADICADO_SUFFIX = {
    TipoPQRS.PETICION.value: "P",
    TipoPQRS.QUEJA.value: "Q",
    TipoPQRS.RECLAMO.value: "R",
    TipoPQRS.SUGERENCIA.value: "S",
    TipoPQRS.OTRO.value: "O",
}


def _generar_radicado(pqrs_id: int, tipo: str) -> str:
    return f"RAD-{pqrs_id:06d}{_RADICADO_SUFFIX.get(tipo, 'O')}"


def _producto_pqrs_desde_create(db: Session, p: ProductoPQRSCreate) -> ProductoPQRS:
    if p.producto_catalogo_id is not None:
        pc = db.get(ProductoCatalogo, p.producto_catalogo_id)
        if not pc or not pc.activo:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Producto de cat?logo no v?lido o inactivo.",
            )
        return ProductoPQRS(
            nombre_producto=pc.nombre,
            cantidad=p.cantidad,
            producto_catalogo_id=pc.id,
            numero_factura=(p.numero_factura or "").strip() or None,
            lote=(p.lote or "").strip() or None,
            comentario=(p.comentario or "").strip() or None,
        )
    return ProductoPQRS(
        nombre_producto=p.nombre_producto.strip(),
        cantidad=p.cantidad,
        producto_catalogo_id=None,
        numero_factura=(p.numero_factura or "").strip() or None,
        lote=(p.lote or "").strip() or None,
        comentario=(p.comentario or "").strip() or None,
    )


def _get_pqrs_or_404(db: Session, pqrs_id: int) -> PQRS:
    pqrs = db.execute(
        select(PQRS)
        .where(PQRS.id == pqrs_id)
        .options(
            selectinload(PQRS.cliente),
            selectinload(PQRS.inconformidad).selectinload(Inconformidad.area),
            selectinload(PQRS.vendedor),
            selectinload(PQRS.productos),
            selectinload(PQRS.evidencias),
            selectinload(PQRS.seguimientos).selectinload(Seguimiento.usuario),
        )
    ).scalar_one_or_none()
    if not pqrs:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PQRS no encontrada")
    return pqrs


def _producto_email_label(producto: ProductoPQRS) -> str:
    cantidad = str(producto.cantidad).rstrip("0").rstrip(".")
    extras = []
    if producto.numero_factura:
        extras.append(f"Factura: {producto.numero_factura}")
    if producto.lote:
        extras.append(f"Lote: {producto.lote}")
    if producto.comentario:
        extras.append(f"Comentario: {producto.comentario}")
    detalle = f" ({' | '.join(extras)})" if extras else ""
    return f"{producto.nombre_producto} - Cantidad: {cantidad or producto.cantidad}{detalle}"


def _evidencia_email_data(evidencia: Evidencia) -> dict[str, str | None]:
    return {
        "nombre": evidencia.nombre_original,
        "url": evidencia.archivo_url,
        "content_type": evidencia.content_type,
    }


def _notify_area_for_pqrs(db: Session, pqrs: PQRS) -> None:
    _ = db
    inc = pqrs.inconformidad
    if not inc or not inc.area:
        return

    area_emails = settings.emails_for_area(inc.area.codigo)
    if not area_emails:
        # Evita ?silencios?: deja pista clara en logs
        from loguru import logger

        logger.warning(
            f"No hay correos configurados para el ?rea '{inc.area.codigo}'. "
            f"Revisa CALIDAD_EMAILS / LOGISTICA_EMAILS / COMERCIAL_EMAILS en .env."
        )
        return

    cliente_nombre = ""
    if pqrs.cliente:
        cliente_nombre = f"{pqrs.cliente.nombre} {pqrs.cliente.apellidos or ''}".strip()

    email_service.notify_quality_complaint_created(
        to_emails=area_emails,
        area_nombre=inc.area.nombre,
        radicado=pqrs.radicado or _generar_radicado(pqrs.id, pqrs.tipo),
        tipo=pqrs.tipo,
        cliente=cliente_nombre,
        factura=pqrs.numero_factura or (pqrs.productos[0].numero_factura if pqrs.productos else None),
        lote=pqrs.lote or (pqrs.productos[0].lote if pqrs.productos else None),
        inconformidad=inc.nombre,
        productos=[_producto_email_label(producto) for producto in pqrs.productos],
        evidencias=[_evidencia_email_data(evidencia) for evidencia in pqrs.evidencias],
        descripcion=pqrs.descripcion,
        fecha_creacion=pqrs.fecha_creacion,
    )


def notify_calidad_for_pqrs(db: Session, pqrs_id: int) -> None:
    pqrs = _get_pqrs_or_404(db, pqrs_id)
    _notify_area_for_pqrs(db, pqrs)


def _assert_cliente_usable_por_vendedor(db: Session, cliente: Cliente, vendedor: Usuario) -> None:
    if vendedor.rol != RolUsuario.VENDEDOR.value:
        return
    if not cliente.activo:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Este cliente est? deshabilitado y no puede usarse en nuevas PQRS.",
        )
    ok = False
    if cliente.vendedor_asignado_id == vendedor.id:
        ok = True
    else:
        row = db.execute(
            select(PQRS.id)
            .where(PQRS.cliente_id == cliente.id, PQRS.vendedor_id == vendedor.id)
            .limit(1)
        ).first()
        if row is not None:
            ok = True
    if not ok:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "No puedes crear PQRS para este cliente.",
        )


def create_pqrs(db: Session, data: PQRSCreate, creador: Usuario) -> PQRS:
    cliente = db.get(Cliente, data.cliente_id)
    if not cliente:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cliente no existe.")
    _assert_cliente_usable_por_vendedor(db, cliente, creador)

    primer_producto = data.productos[0] if data.productos else None
    pqrs = PQRS(
        cliente_id=data.cliente_id,
        vendedor_id=data.vendedor_id or (creador.id if creador.rol == "VENDEDOR" else None),
        tipo=data.tipo.value,
        inconformidad_id=data.inconformidad_id,
        numero_factura=data.numero_factura or (primer_producto.numero_factura if primer_producto else None),
        lote=data.lote or (primer_producto.lote if primer_producto else None),
        descripcion=data.descripcion,
        estado=EstadoPQRS.ABIERTA.value,
    )
    for prod in data.productos:
        pqrs.productos.append(_producto_pqrs_desde_create(db, prod))

    pqrs.seguimientos.append(
        Seguimiento(
            estado=EstadoPQRS.ABIERTA.value,
            descripcion="PQRS creada.",
            usuario_id=creador.id,
        )
    )
    db.add(pqrs)
    db.flush()
    pqrs.radicado = _generar_radicado(pqrs.id, pqrs.tipo)
    db.commit()
    db.refresh(pqrs)

    return _get_pqrs_or_404(db, pqrs.id)


def list_pqrs(
    db: Session,
    *,
    estado: EstadoPQRS | None = None,
    tipo: TipoPQRS | None = None,
    cliente_id: int | None = None,
    vendedor_id: int | None = None,
    fecha_desde: datetime | None = None,
    fecha_hasta: datetime | None = None,
    q: str | None = None,
    page: int = 1,
    size: int = 20,
    actor: Usuario | None = None,
) -> tuple[list[dict[str, Any]], int]:
    if actor is not None and actor.rol == RolUsuario.VENDEDOR.value:
        vendedor_id = actor.id

    stmt = (
        select(
            PQRS,
            Cliente.nombre,
            Cliente.apellidos,
            Usuario.nombre.label("vendedor_nombre"),
        )
        .join(Cliente, Cliente.id == PQRS.cliente_id)
        .outerjoin(Usuario, Usuario.id == PQRS.vendedor_id)
        .outerjoin(Inconformidad, Inconformidad.id == PQRS.inconformidad_id)
        .options(
            selectinload(PQRS.inconformidad).selectinload(Inconformidad.area),
        )
    )
    conditions = []
    if estado:
        conditions.append(PQRS.estado == estado.value)
    if tipo:
        conditions.append(PQRS.tipo == tipo.value)
    if cliente_id:
        conditions.append(PQRS.cliente_id == cliente_id)
    if vendedor_id:
        conditions.append(PQRS.vendedor_id == vendedor_id)
    if fecha_desde:
        conditions.append(PQRS.fecha_creacion >= fecha_desde)
    if fecha_hasta:
        conditions.append(PQRS.fecha_creacion <= fecha_hasta)
    if q:
        like = f"%{q.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(PQRS.radicado).like(like),
                func.lower(PQRS.numero_factura).like(like),
                func.lower(PQRS.descripcion).like(like),
                func.lower(Cliente.nombre).like(like),
                func.lower(Cliente.nit).like(like),
            )
        )
    if conditions:
        stmt = stmt.where(and_(*conditions))

    count_stmt = select(func.count(PQRS.id))
    if conditions:
        count_stmt = (
            select(func.count(PQRS.id))
            .select_from(PQRS)
            .join(Cliente, Cliente.id == PQRS.cliente_id)
            .outerjoin(Usuario, Usuario.id == PQRS.vendedor_id)
            .where(and_(*conditions))
        )
    total = int(db.execute(count_stmt).scalar_one())

    rows = db.execute(
        stmt.order_by(PQRS.fecha_creacion.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()

    items: list[dict[str, Any]] = []
    for row in rows:
        pqrs: PQRS = row[0]
        cliente_nombre = f"{row[1] or ''} {row[2] or ''}".strip()
        inc_responsable = pqrs.inconformidad
        items.append(
            {
                "id": pqrs.id,
                "radicado": pqrs.radicado or _generar_radicado(pqrs.id, pqrs.tipo),
                "tipo": pqrs.tipo,
                "estado": pqrs.estado,
                "cliente_id": pqrs.cliente_id,
                "cliente_nombre": cliente_nombre,
                "vendedor_id": pqrs.vendedor_id,
                "vendedor_nombre": row[3],
                "area_codigo": inc_responsable.area.codigo if inc_responsable else None,
                "area_nombre": inc_responsable.area.nombre if inc_responsable else None,
                "numero_factura": pqrs.numero_factura,
                "fecha_creacion": pqrs.fecha_creacion,
                "fecha_cierre": pqrs.fecha_cierre,
            }
        )
    return items, total


def get_pqrs_detail(db: Session, pqrs_id: int, actor: Usuario | None = None) -> PQRS:
    pqrs = _get_pqrs_or_404(db, pqrs_id)
    if (
        actor is not None
        and actor.rol == RolUsuario.VENDEDOR.value
        and pqrs.vendedor_id != actor.id
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "No tienes permisos para ver esta PQRS.",
        )
    return pqrs


def update_pqrs(
    db: Session, pqrs_id: int, data: PQRSUpdate, actor: Usuario
) -> PQRS:
    pqrs = _get_pqrs_or_404(db, pqrs_id)
    if actor.rol != RolUsuario.ADMINISTRADOR.value:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Solo el administrador puede editar una PQRS.",
        )
    changes = data.model_dump(exclude_unset=True)

    if pqrs.estado in (EstadoPQRS.CERRADA.value, EstadoPQRS.RECHAZADA.value) and changes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La PQRS est? cerrada o rechazada; no admite modificaciones.",
        )

    if "estado" in changes and changes["estado"] is not None:
        new_state = changes["estado"].value if hasattr(changes["estado"], "value") else changes["estado"]
        if new_state != pqrs.estado:
            pqrs.estado = new_state
            if new_state in (EstadoPQRS.CERRADA.value, EstadoPQRS.RECHAZADA.value):
                pqrs.fecha_cierre = datetime.now(tz=timezone.utc)
            pqrs.seguimientos.append(
                Seguimiento(
                    estado=new_state,
                    descripcion=data.descripcion or f"Estado actualizado a {new_state}",
                    usuario_id=actor.id,
                )
            )

    for key in ("descripcion", "numero_factura", "lote", "inconformidad_id", "vendedor_id"):
        if key in changes and changes[key] is not None:
            setattr(pqrs, key, changes[key])

    db.commit()
    db.refresh(pqrs)

    if pqrs.estado == EstadoPQRS.CERRADA.value and pqrs.cliente and pqrs.cliente.correo:
        email_service.notify_pqrs_closed(
            to_email=pqrs.cliente.correo,
            radicado=pqrs.radicado or _generar_radicado(pqrs.id, pqrs.tipo),
            tipo=pqrs.tipo,
            respuesta=data.descripcion or "Se cerr? la solicitud.",
        )
    devolucion_service.ensure_devolucion_pendiente(
        db,
        pqrs,
        usuario_id=actor.id,
        observaciones=data.descripcion,
    )
    return _get_pqrs_or_404(db, pqrs.id)


def _deny_if_vendedor(actor: Usuario | None) -> None:
    if actor is not None and actor.rol == RolUsuario.VENDEDOR.value:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "El vendedor no puede modificar esta PQRS despu?s de creada.",
        )


def add_productos(
    db: Session, pqrs_id: int, productos: list[ProductoPQRSCreate], actor: Usuario | None = None
) -> list[ProductoPQRS]:
    _deny_if_vendedor(actor)
    pqrs = _get_pqrs_or_404(db, pqrs_id)
    if pqrs.estado in (EstadoPQRS.CERRADA.value, EstadoPQRS.RECHAZADA.value):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La PQRS est? cerrada o rechazada; no se pueden agregar productos.",
        )
    creados: list[ProductoPQRS] = []
    for p in productos:
        obj = _producto_pqrs_desde_create(db, p)
        obj.pqrs_id = pqrs.id
        db.add(obj)
        creados.append(obj)
    db.commit()
    for c in creados:
        db.refresh(c)
    return creados


def delete_producto(
    db: Session, pqrs_id: int, producto_id: int, actor: Usuario | None = None
) -> None:
    _deny_if_vendedor(actor)
    pqrs = _get_pqrs_or_404(db, pqrs_id)
    if pqrs.estado in (EstadoPQRS.CERRADA.value, EstadoPQRS.RECHAZADA.value):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La PQRS est? cerrada o rechazada; no se pueden eliminar productos.",
        )
    prod = db.execute(
        select(ProductoPQRS).where(
            ProductoPQRS.id == producto_id, ProductoPQRS.pqrs_id == pqrs_id
        )
    ).scalar_one_or_none()
    if not prod:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    db.delete(prod)
    db.commit()


def add_evidencia(
    db: Session,
    pqrs_id: int,
    archivo_url: str,
    nombre_original: str | None,
    content_type: str | None,
    actor: Usuario | None = None,
    carga_inicial: bool = False,
) -> Evidencia:
    pqrs = _get_pqrs_or_404(db, pqrs_id)
    if actor is not None and actor.rol == RolUsuario.VENDEDOR.value:
        allowed_initial_upload = (
            carga_inicial
            and pqrs.vendedor_id == actor.id
            and pqrs.estado == EstadoPQRS.ABIERTA.value
        )
        if not allowed_initial_upload:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "El vendedor solo puede subir evidencias durante la creaci?n inicial de la PQRS.",
            )
    if pqrs.estado in (EstadoPQRS.CERRADA.value, EstadoPQRS.RECHAZADA.value):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La PQRS est? cerrada o rechazada; no se pueden subir evidencias.",
        )
    ev = Evidencia(
        pqrs_id=pqrs_id,
        archivo_url=archivo_url,
        nombre_original=nombre_original,
        content_type=content_type,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def add_seguimiento(
    db: Session, pqrs_id: int, estado: EstadoPQRS, descripcion: str | None, actor: Usuario
) -> Seguimiento:
    if actor.rol not in (
        RolUsuario.ADMINISTRADOR.value,
        RolUsuario.ADMINISTRATIVO_COMERCIAL.value,
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Solo administrador o administrativo comercial pueden registrar seguimiento.",
        )
    pqrs = _get_pqrs_or_404(db, pqrs_id)
    if pqrs.estado in (EstadoPQRS.CERRADA.value, EstadoPQRS.RECHAZADA.value):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La PQRS est? cerrada o rechazada; no se puede registrar seguimiento.",
        )
    seg = Seguimiento(
        pqrs_id=pqrs.id,
        usuario_id=actor.id,
        estado=estado.value,
        descripcion=descripcion,
    )
    db.add(seg)

    if pqrs.estado != estado.value:
        pqrs.estado = estado.value
        if estado in (EstadoPQRS.CERRADA, EstadoPQRS.RECHAZADA):
            pqrs.fecha_cierre = datetime.now(tz=timezone.utc)

    db.commit()
    db.refresh(seg)
    db.refresh(pqrs)
    devolucion_service.ensure_devolucion_pendiente(
        db,
        pqrs,
        usuario_id=actor.id,
        observaciones=descripcion,
    )
    return seg


def listar_seguimientos(db: Session, pqrs_id: int) -> list[Seguimiento]:
    _get_pqrs_or_404(db, pqrs_id)
    return list(
        db.execute(
            select(Seguimiento)
            .where(Seguimiento.pqrs_id == pqrs_id)
            .order_by(Seguimiento.fecha.desc())
            .options(selectinload(Seguimiento.usuario))
        ).scalars()
    )


