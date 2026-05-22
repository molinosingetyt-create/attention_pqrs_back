"""Servicio de devoluciones (radicado separado del historial PQRS)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import EstadoPQRS, RolUsuario
from app.models import Area, Cliente, Devolucion, Inconformidad, PQRS, ProductoPQRS
from app.models.producto_catalogo import ProductoCatalogo
from app.models.usuario import Usuario
from app.schemas.devolucion import DevolucionRegistroIn
from app.schemas.pqrs import ProductoPQRSOut


_DEV_PREFIX = "DEV-"


def _radicado_pqrs(pqrs: PQRS) -> str:
    suffix = {
        "PETICION": "P",
        "QUEJA": "Q",
        "RECLAMO": "R",
        "SUGERENCIA": "S",
        "OTRO": "O",
    }.get(pqrs.tipo, "O")
    return pqrs.radicado or f"RAD-{pqrs.id:06d}{suffix}"


def _siguiente_codigo_devolucion(db: Session) -> str:
    codigos = (
        db.execute(
            select(Devolucion.codigo_devolucion).where(
                Devolucion.codigo_devolucion.isnot(None)
            )
        )
        .scalars()
        .all()
    )
    consecutivos = [
        int(codigo.removeprefix(_DEV_PREFIX))
        for codigo in codigos
        if codigo.startswith(_DEV_PREFIX)
        and codigo.removeprefix(_DEV_PREFIX).isdigit()
    ]
    siguiente = (max(consecutivos) if consecutivos else 0) + 1
    return f"{_DEV_PREFIX}{siguiente:06d}"


def _productos_pqrs(db: Session, pqrs_id: int) -> list[dict[str, Any]]:
    rows = (
        db.execute(
            select(ProductoPQRS)
            .where(ProductoPQRS.pqrs_id == pqrs_id)
            .options(
                selectinload(ProductoPQRS.producto_catalogo).selectinload(
                    ProductoCatalogo.categoria
                )
            )
        )
        .scalars()
        .all()
    )
    out: list[dict[str, Any]] = []
    for p in rows:
        cat = None
        if p.producto_catalogo and p.producto_catalogo.categoria:
            cat = p.producto_catalogo.categoria.nombre
        dto = ProductoPQRSOut(
            id=p.id,
            nombre_producto=p.nombre_producto,
            cantidad=float(p.cantidad),
            producto_catalogo_id=p.producto_catalogo_id,
            numero_factura=p.numero_factura,
            lote=p.lote,
            comentario=p.comentario,
            categoria_nombre=cat,
        )
        out.append(dto.model_dump())
    return out


def _primer_producto_pqrs(db: Session, pqrs_id: int) -> ProductoPQRS | None:
    return (
        db.execute(
            select(ProductoPQRS)
            .where(ProductoPQRS.pqrs_id == pqrs_id)
            .options(
                selectinload(ProductoPQRS.producto_catalogo).selectinload(
                    ProductoCatalogo.categoria
                )
            )
            .order_by(ProductoPQRS.id)
            .limit(1)
        )
        .scalars()
        .first()
    )


def _infer_producto_devolucion(
    p: ProductoPQRS | None,
) -> Literal["TRIGO", "MAIZ", "PASTA_CORTA", "PASTA_LARGA"]:
    if p and p.producto_catalogo and p.producto_catalogo.categoria:
        cat = p.producto_catalogo.categoria.nombre.upper()
        if "MAIZ" in cat or "MAÍZ" in cat:
            return "MAIZ"
        if "PASTA" in cat:
            return "PASTA_CORTA"
        return "TRIGO"
    if p and p.nombre_producto:
        n = p.nombre_producto.upper()
        if "MAIZ" in n or "MAÍZ" in n or "MAZ" in n:
            return "MAIZ"
        if "PASTA" in n or "ESPAGUET" in n or "CODITO" in n:
            return "PASTA_CORTA"
    return "TRIGO"


def _fecha_recibo_desde_datos(datos: dict[str, Any] | None) -> datetime | None:
    if not datos:
        return None
    raw = datos.get("fecha_recibo_devolucion")
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def ensure_devolucion_pendiente(
    db: Session,
    pqrs: PQRS,
    *,
    usuario_id: int | None = None,
    observaciones: str | None = None,
) -> None:
    """Crea devolución pendiente al cerrar PQRS con inconformidad (fecha_registro = cierre)."""
    if pqrs.estado != EstadoPQRS.CERRADA.value:
        return
    if not pqrs.inconformidad_id:
        return
    exists = (
        db.execute(select(Devolucion.id).where(Devolucion.pqrs_id == pqrs.id))
        .scalar_one_or_none()
    )
    if exists:
        return
    now = datetime.now(timezone.utc)
    db.add(
        Devolucion(
            pqrs_id=pqrs.id,
            pendiente=True,
            aplica=True,
            observaciones=observaciones,
            fecha_decision=now,
            fecha_registro=now,
        )
    )
    db.commit()


def list_devoluciones_pendientes(
    db: Session, actor: Usuario | None = None
) -> list[dict[str, Any]]:
    stmt = (
        select(Devolucion, PQRS, Cliente, Area, Inconformidad)
        .join(PQRS, PQRS.id == Devolucion.pqrs_id)
        .join(Cliente, Cliente.id == PQRS.cliente_id)
        .outerjoin(Inconformidad, Inconformidad.id == PQRS.inconformidad_id)
        .outerjoin(Area, Area.id == Inconformidad.area_id)
        .where(PQRS.inconformidad_id.isnot(None))
        .order_by(Devolucion.pendiente.desc(), Devolucion.fecha_registro.desc())
    )
    if actor is not None and actor.rol == RolUsuario.CALIDAD.value:
        stmt = stmt.where(Area.codigo == "CALIDAD")

    rows = db.execute(stmt).all()
    out: list[dict[str, Any]] = []
    for dev, pqrs, cliente, area, inc in rows:
        apellidos = (cliente.apellidos or "").strip()
        primer = _primer_producto_pqrs(db, pqrs.id)
        producto_queja = (
            (primer.nombre_producto or "").strip() if primer else None
        ) or None
        fecha_servicio = None
        if not dev.pendiente:
            fecha_servicio = _fecha_recibo_desde_datos(
                dev.datos_registro
            ) or dev.fecha_decision
        out.append(
            {
                "devolucion_id": dev.id,
                "codigo_devolucion": dev.codigo_devolucion,
                "pqrs_id": pqrs.id,
                "radicado": _radicado_pqrs(pqrs),
                "tipo": pqrs.tipo,
                "estado": pqrs.estado,
                "cliente_nombre": cliente.nombre,
                "cliente_apellidos": apellidos,
                "fecha_cierre": pqrs.fecha_cierre,
                "fecha_registro": dev.fecha_registro,
                "fecha_servicio_generado": fecha_servicio,
                "producto_queja": producto_queja,
                "area_codigo": area.codigo if area else "",
                "area_nombre": area.nombre if area else "—",
                "inconformidad_nombre": inc.nombre if inc else "—",
                "inconformidad_descripcion": inc.descripcion if inc else None,
                "pendiente": dev.pendiente,
                "aplica": dev.aplica,
            }
        )
    return out


def get_devolucion_detalle(db: Session, devolucion_id: int) -> dict[str, Any] | None:
    row = (
        db.execute(
            select(Devolucion, PQRS, Cliente, Area, Inconformidad)
            .join(PQRS, PQRS.id == Devolucion.pqrs_id)
            .join(Cliente, Cliente.id == PQRS.cliente_id)
            .outerjoin(Inconformidad, Inconformidad.id == PQRS.inconformidad_id)
            .outerjoin(Area, Area.id == Inconformidad.area_id)
            .where(Devolucion.id == devolucion_id)
        )
        .first()
    )
    if not row:
        return None
    dev, pqrs, cliente, area, inc = row
    productos = _productos_pqrs(db, pqrs.id)
    apellidos = (cliente.apellidos or "").strip()
    return {
        "id": dev.id,
        "codigo_devolucion": dev.codigo_devolucion,
        "pqrs_id": pqrs.id,
        "pendiente": dev.pendiente,
        "aplica": dev.aplica,
        "observaciones": dev.observaciones,
        "fecha_registro": dev.fecha_registro,
        "fecha_decision": dev.fecha_decision,
        "datos_registro": dev.datos_registro,
        "cliente_nombre": cliente.nombre,
        "cliente_apellidos": apellidos,
        "area_codigo": area.codigo if area else "",
        "area_nombre": area.nombre if area else "—",
        "inconformidad_nombre": inc.nombre if inc else "—",
        "inconformidad_descripcion": inc.descripcion if inc else None,
        "pqrs": {
            "id": pqrs.id,
            "radicado": _radicado_pqrs(pqrs),
            "tipo": pqrs.tipo,
            "estado": pqrs.estado,
            "numero_factura": pqrs.numero_factura,
            "lote": pqrs.lote,
            "descripcion": pqrs.descripcion,
            "fecha_cierre": pqrs.fecha_cierre,
            "productos": productos,
        },
    }


def guardar_registro_radico(
    db: Session,
    devolucion_id: int,
    data: DevolucionRegistroIn,
    *,
    usuario_id: int | None,
) -> Devolucion:
    dev = db.get(Devolucion, devolucion_id)
    if not dev:
        raise ValueError("Devolución no encontrada")
    if not dev.pendiente:
        raise ValueError("Esta devolución ya fue radicada")
    pqrs = db.get(PQRS, dev.pqrs_id)
    if not pqrs:
        raise ValueError("PQRS no encontrada")
    if pqrs.estado != EstadoPQRS.CERRADA.value:
        raise ValueError("Solo se radica devolución para PQRS cerrada")

    _ = usuario_id

    now = datetime.now(timezone.utc)
    primer = _primer_producto_pqrs(db, pqrs.id)
    producto_tipo = _infer_producto_devolucion(primer)
    registro: dict[str, Any] = data.model_dump(mode="json")
    registro["producto_tipo"] = producto_tipo
    dev.codigo_devolucion = dev.codigo_devolucion or _siguiente_codigo_devolucion(db)
    registro["codigo_devolucion"] = dev.codigo_devolucion
    registro["fecha_recibo_devolucion"] = now.isoformat()
    dev.datos_registro = registro
    dev.observaciones = data.comentario_devolucion or data.detalle_respuesta
    dev.pendiente = False
    dev.fecha_decision = now
    db.flush()
    return dev
