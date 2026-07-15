"""Generación de PDFs oficiales PQRS recreados desde cero (sin plantillas)."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.cliente import Cliente
from app.models.devolucion import Devolucion
from app.models.pqrs import PQRS
from app.models.producto_catalogo import ProductoCatalogo
from app.models.producto_pqrs import ProductoPQRS
from app.models.seguimiento import Seguimiento
from app.services import pqrs_service

_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "pdf"
_LOGO_PATH = _ASSETS / "logo-molinos.jpeg"
_TZ = ZoneInfo("America/Bogota")

_BLACK = colors.black
_GRAY_HEADER = colors.Color(0.82, 0.82, 0.82)
_LIGHT_GRAY = colors.Color(0.94, 0.94, 0.94)


def _fmt_fecha(dt: datetime | None) -> str:
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(_TZ).strftime("%d/%m/%Y")


def _fmt_fecha_hora(dt: datetime | None) -> str:
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(_TZ).strftime("%d/%m/%Y %H:%M")


def _cliente_nombre(cliente: Cliente | None) -> str:
    if not cliente:
        return ""
    return f"{cliente.nombre} {(cliente.apellidos or '').strip()}".strip()


def _radicado(pqrs: PQRS) -> str:
    return pqrs.radicado or pqrs_service._generar_radicado(pqrs.id, pqrs.tipo)


def _recibida_por(pqrs: PQRS) -> str:
    if pqrs.vendedor and pqrs.vendedor.nombre:
        return pqrs.vendedor.nombre
    for seg in sorted(pqrs.seguimientos, key=lambda s: s.fecha):
        if seg.usuario and seg.usuario.nombre:
            return seg.usuario.nombre
    return "Plataforma PQRS"


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCenter",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            alignment=TA_CENTER,
            leading=11,
        ),
        "title_sub": ParagraphStyle(
            "TitleSub",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            alignment=TA_CENTER,
            leading=10,
        ),
        "meta": ParagraphStyle(
            "MetaRight",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            alignment=TA_CENTER,
            leading=10,
        ),
        "section": ParagraphStyle(
            "SectionHeader",
            parent=base["Normal"],
            fontName="Helvetica-BoldOblique",
            fontSize=9,
            alignment=TA_CENTER,
            leading=11,
        ),
        "label": ParagraphStyle(
            "Label",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
        ),
        "value": ParagraphStyle(
            "Value",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            alignment=TA_CENTER,
            leading=10,
        ),
    }


def _logo_image(max_w: float = 55, max_h: float = 45) -> Image | Paragraph:
    styles = _styles()
    if _LOGO_PATH.is_file():
        img = Image(str(_LOGO_PATH))
        # Deja un margen mínimo dentro del recuadro para no sobrepasar bordes.
        ratio = min((max_w - 2) / img.imageWidth, (max_h - 2) / img.imageHeight)
        img.drawWidth = img.imageWidth * ratio
        img.drawHeight = img.imageHeight * ratio
        img.hAlign = "CENTER"
        return img
    return Paragraph("MOLINOS<br/>DEL ATLÁNTICO", styles["meta"])


def _etiqueta_tipo(tipo: str | None) -> str:
    labels = {
        "PETICION": "Petición",
        "QUEJA": "Queja",
        "RECLAMO": "Reclamo",
        "SUGERENCIA": "Sugerencia",
        "OTRO": "Otro",
    }
    key = str(tipo or "").upper()
    return labels.get(key, key or "—")


def _checkbox(selected: bool) -> str:
    return "[X]" if selected else "[ ]"


def _load_pqrs(db: Session, pqrs_id: int) -> PQRS:
    pqrs = db.execute(
        select(PQRS)
        .where(PQRS.id == pqrs_id)
        .options(
            selectinload(PQRS.cliente),
            selectinload(PQRS.vendedor),
            selectinload(PQRS.inconformidad),
            selectinload(PQRS.productos)
            .selectinload(ProductoPQRS.producto_catalogo)
            .selectinload(ProductoCatalogo.categoria),
            selectinload(PQRS.devolucion),
            selectinload(PQRS.seguimientos).selectinload(Seguimiento.usuario),
        )
    ).scalar_one_or_none()
    if not pqrs:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PQRS no encontrada.")
    return pqrs


def _categoria_producto(p: ProductoPQRS) -> str:
    cat = None
    if p.producto_catalogo and p.producto_catalogo.categoria:
        cat = p.producto_catalogo.categoria.nombre
    return (cat or "").strip()


def _referencia_producto(p: ProductoPQRS) -> str:
    if p.producto_catalogo and p.producto_catalogo.nombre:
        return p.producto_catalogo.nombre.strip()
    return (p.nombre_producto or "").strip()


def _productos_devolucion(pqrs: PQRS, dev: Devolucion | None) -> list[dict[str, Any]]:
    if dev and dev.datos_registro:
        raw = dev.datos_registro.get("productos_devolucion")
        if isinstance(raw, list) and raw:
            return raw
        producto = dev.datos_registro.get("producto")
        if producto:
            return [
                {
                    "producto": producto,
                    "cantidad": dev.datos_registro.get("cantidad"),
                    "numero_factura": dev.datos_registro.get("numero_factura"),
                    "referencia": dev.datos_registro.get("lote") or "",
                }
            ]
    out: list[dict[str, Any]] = []
    for p in pqrs.productos:
        out.append(
            {
                "producto": _categoria_producto(p) or p.nombre_producto,
                "referencia": _referencia_producto(p),
                "cantidad": p.cantidad,
                "numero_factura": p.numero_factura or pqrs.numero_factura,
            }
        )
    return out


def _build_formato_pqrs(pqrs: PQRS) -> bytes:
    styles = _styles()
    cliente = pqrs.cliente
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )
    page_w = letter[0] - 24 * mm
    story: list[Any] = []

    # ---- Header ----
    logo_col_w = page_w * 0.20
    header_h = 62
    logo = _logo_image(logo_col_w - 6, header_h - 6)
    titulo = Paragraph("MOLINOS DEL ATLANTICO S.A.S", styles["title"])
    subtitulo = Paragraph(
        "REGISTRO DE TRATAMIENTO DE PETICIONES, QUEJAS, RECLAMOS O<br/>SUGERENCIAS (PQRS)",
        styles["title_sub"],
    )
    version = Paragraph("VERSION 8<br/>2026-07-10", styles["meta"])
    header = Table(
        [[logo, [titulo, Spacer(1, 2), subtitulo], version]],
        colWidths=[logo_col_w, page_w * 0.58, page_w * 0.22],
        rowHeights=[header_h],
    )
    header.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.7, _BLACK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (0, 0), 3),
                ("RIGHTPADDING", (0, 0), (0, 0), 3),
                ("TOPPADDING", (0, 0), (0, 0), 3),
                ("BOTTOMPADDING", (0, 0), (0, 0), 3),
                ("LEFTPADDING", (1, 0), (-1, -1), 4),
                ("RIGHTPADDING", (1, 0), (-1, -1), 4),
                ("TOPPADDING", (1, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (1, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(header)

    # ---- Fecha radicación + radicado ----
    fecha = Table(
        [
            [
                Paragraph(
                    f"<b>FECHA DE RADICACIÓN DE LA PQRS:</b>  {_fmt_fecha_hora(pqrs.fecha_creacion)}",
                    styles["value"],
                ),
                Paragraph(
                    f"<b>RADICADO:</b>  {_radicado(pqrs)}",
                    styles["value"],
                ),
            ]
        ],
        colWidths=[page_w * 0.62, page_w * 0.38],
    )
    fecha.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _BLACK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(fecha)

    # ---- Tipo + Motivo (texto, no checks) ----
    motivo_nombre = (
        pqrs.inconformidad.nombre if pqrs.inconformidad and pqrs.inconformidad.nombre else "—"
    )
    tipo_tbl = Table(
        [
            [
                Paragraph(
                    f"<b>TIPO DE PQRS:</b>  {_etiqueta_tipo(pqrs.tipo)}",
                    styles["value"],
                ),
                Paragraph(
                    f"<b>MOTIVO DE LA PQRS:</b>  {motivo_nombre}",
                    styles["value"],
                ),
            ]
        ],
        colWidths=[page_w * 0.40, page_w * 0.60],
    )
    tipo_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _BLACK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(tipo_tbl)

    # ---- Cliente ----
    cliente_header = Table(
        [[Paragraph("CLIENTE QUIEN PRESENTA LA PQRS", styles["section"])]],
        colWidths=[page_w],
    )
    cliente_header.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("BACKGROUND", (0, 0), (-1, -1), _GRAY_HEADER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(cliente_header)

    razon = cliente.nombre if cliente else ""
    contacto = (cliente.apellidos or "") if cliente else ""
    ciudad = (cliente.ciudad or "") if cliente else ""
    nit = cliente.nit if cliente else ""
    telefono = (cliente.telefono or "") if cliente else ""

    cliente_body = Table(
        [
            [
                Paragraph(f"<b>RAZÓN SOCIAL:</b> {razon}", styles["value"]),
                Paragraph(f"<b>NOMBRE DE CONTACTO:</b> {contacto}", styles["value"]),
                Paragraph(f"<b>CIUDAD:</b> {ciudad}", styles["value"]),
            ],
            [
                Paragraph(f"<b>CÉDULA O NIT:</b> {nit}", styles["value"]),
                Paragraph(f"<b>TELÉFONOS:</b> {telefono}", styles["value"]),
                "",
            ],
            [
                Paragraph(
                    f"<b>PQRS RECIBIDA POR:</b> {_recibida_por(pqrs)}",
                    styles["value"],
                ),
                "",
                "",
            ],
        ],
        colWidths=[page_w * 0.38, page_w * 0.37, page_w * 0.25],
    )
    cliente_body.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _BLACK),
                ("SPAN", (0, 2), (-1, 2)),
                ("SPAN", (0, 1), (0, 1)),
                ("SPAN", (1, 1), (2, 1)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(cliente_body)

    # ---- Medio de comunicación ----
    medio_h = Table(
        [[Paragraph("MEDIO DE COMUNICACIÓN POR EL QUE SE RECIBE LA PQRS", styles["section"])]],
        colWidths=[page_w],
    )
    medio_h.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("BACKGROUND", (0, 0), (-1, -1), _GRAY_HEADER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(medio_h)
    medios = (
        f"{_checkbox(False)} Presencial   "
        f"{_checkbox(False)} Teléfono   "
        f"{_checkbox(False)} Email - Correo   "
        f"{_checkbox(False)} WhatsApp   "
        f"{_checkbox(False)} Otro ¿Cuál?"
    )
    medio_b = Table([[Paragraph(medios, styles["value"])]], colWidths=[page_w])
    medio_b.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(medio_b)

    # ---- Detalle ----
    det_h = Table(
        [[Paragraph("DETALLE Y/O OBSERVACIONES DE LA PQRS", styles["section"])]],
        colWidths=[page_w],
    )
    det_h.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("BACKGROUND", (0, 0), (-1, -1), _GRAY_HEADER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(det_h)
    desc = (pqrs.descripcion or "").strip() or " "
    det_b = Table(
        [[Paragraph(desc.replace("\n", "<br/>"), styles["value"])]],
        colWidths=[page_w],
        rowHeights=[55],
    )
    det_b.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(det_b)

    # ---- Productos ----
    prod_h = Table(
        [
            [
                Paragraph(
                    "IDENTIFICACIÓN DEL PRODUCTO DE LA PQRS",
                    styles["section"],
                )
            ]
        ],
        colWidths=[page_w],
    )
    prod_h.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("BACKGROUND", (0, 0), (-1, -1), _GRAY_HEADER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(prod_h)

    cols = [page_w * x for x in (0.22, 0.30, 0.12, 0.10, 0.12, 0.14)]
    prod_data: list[list[Any]] = [
        [
            Paragraph("<b>PRODUCTO</b>", styles["small"]),
            Paragraph("<b>REFERENCIA</b>", styles["small"]),
            Paragraph("<b>LOTE</b>", styles["small"]),
            Paragraph("<b>VENCE</b>", styles["small"]),
            Paragraph("<b>CANTIDAD</b>", styles["small"]),
            Paragraph("<b>FACTURA</b>", styles["small"]),
        ]
    ]
    productos = list(pqrs.productos or [])
    for i in range(max(5, len(productos))):
        if i < len(productos):
            p = productos[i]
            cant = str(p.cantidad).rstrip("0").rstrip(".")
            prod_data.append(
                [
                    Paragraph(_categoria_producto(p) or "—", styles["small"]),
                    Paragraph(_referencia_producto(p), styles["small"]),
                    Paragraph(p.lote or "", styles["small"]),
                    Paragraph("", styles["small"]),
                    Paragraph(cant, styles["small"]),
                    Paragraph(p.numero_factura or pqrs.numero_factura or "", styles["small"]),
                ]
            )
        else:
            prod_data.append(["", "", "", "", "", ""])

    prod_tbl = Table(prod_data, colWidths=cols)
    prod_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _BLACK),
                ("BACKGROUND", (0, 0), (-1, 0), _LIGHT_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("ROWHEIGHT", (0, 1), (-1, -1), 16),
            ]
        )
    )
    story.append(prod_tbl)

    comentarios = [
        (p.comentario or "").strip()
        for p in productos
        if (p.comentario or "").strip()
    ]
    obs = " · ".join(comentarios) if comentarios else ""
    obs_tbl = Table(
        [[Paragraph(f"<b>Observaciones:</b> {obs}", styles["value"])]],
        colWidths=[page_w],
        rowHeights=[40],
    )
    obs_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(obs_tbl)

    doc.build(story)
    return buf.getvalue()


def _build_autorizacion_devolucion(pqrs: PQRS) -> bytes:
    styles = _styles()
    cliente = pqrs.cliente
    dev = pqrs.devolucion
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    page_w = A4[0] - 28 * mm
    story: list[Any] = []

    logo_col_w = page_w * 0.28
    header_h = 78
    logo = _logo_image(logo_col_w - 6, header_h - 6)
    titulo = Paragraph(
        f"AUTORIZACION DE DEVOLUCIONES<br/><font size='9'>{_radicado(pqrs)}</font>",
        styles["title"],
    )
    version = Paragraph("Version 1<br/>2014-05-20", styles["meta"])
    header = Table(
        [[logo, titulo, version]],
        colWidths=[logo_col_w, page_w * 0.50, page_w * 0.22],
        rowHeights=[header_h],
    )
    header.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.7, _BLACK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (0, 0), 3),
                ("RIGHTPADDING", (0, 0), (0, 0), 3),
                ("TOPPADDING", (0, 0), (0, 0), 3),
                ("BOTTOMPADDING", (0, 0), (0, 0), 3),
                ("LEFTPADDING", (1, 0), (-1, -1), 4),
                ("RIGHTPADDING", (1, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 8))

    fecha = _fmt_fecha(pqrs.fecha_cierre or pqrs.fecha_creacion)
    if dev and dev.datos_registro:
        raw_fecha = dev.datos_registro.get("fecha_recibo_devolucion")
        if isinstance(raw_fecha, str):
            try:
                fecha = _fmt_fecha(
                    datetime.fromisoformat(raw_fecha.replace("Z", "+00:00"))
                )
            except ValueError:
                pass

    info = Table(
        [
            [
                Paragraph(f"<b>Fecha:</b> {fecha}", styles["value"]),
                Paragraph(
                    f"<b>Cliente:</b> {_cliente_nombre(cliente)}", styles["value"]
                ),
                Paragraph(
                    f"<b>Nit:</b> {cliente.nit if cliente else ''}", styles["value"]
                ),
            ]
        ],
        colWidths=[page_w * 0.28, page_w * 0.42, page_w * 0.30],
    )
    info.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _BLACK),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(info)

    productos = _productos_devolucion(pqrs, dev)
    prod_data: list[list[Any]] = [
        [
            Paragraph("<b>Producto</b>", styles["value"]),
            Paragraph("<b>Referencia</b>", styles["value"]),
            Paragraph("<b>Cantidad</b>", styles["value"]),
        ]
    ]
    for i in range(max(4, len(productos))):
        if i < len(productos):
            item = productos[i]
            cant = item.get("cantidad")
            cant_s = "" if cant is None else str(cant).rstrip("0").rstrip(".")
            prod_data.append(
                [
                    Paragraph(
                        str(item.get("producto") or item.get("nombre_producto") or ""),
                        styles["small"],
                    ),
                    Paragraph(
                        str(item.get("referencia") or item.get("lote") or ""),
                        styles["small"],
                    ),
                    Paragraph(cant_s, styles["small"]),
                ]
            )
        else:
            prod_data.append(["", "", ""])

    prod_tbl = Table(prod_data, colWidths=[page_w * 0.45, page_w * 0.30, page_w * 0.25])
    prod_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _BLACK),
                ("BACKGROUND", (0, 0), (-1, 0), _LIGHT_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(prod_tbl)

    factura = pqrs.numero_factura or ""
    codigo = ""
    costo = ""
    if productos:
        factura = str(productos[0].get("numero_factura") or factura or "")
    if dev:
        codigo = dev.codigo_devolucion or ""
        if dev.datos_registro:
            costo = str(dev.datos_registro.get("costo") or "")

    factura_tbl = Table(
        [
            [
                Paragraph(f"<b># de Factura</b><br/>{factura}", styles["value"]),
                Paragraph(f"<b># de recibo de caja</b><br/>{codigo}", styles["value"]),
                Paragraph(f"<b>Valor de la devolución</b><br/>{costo}", styles["value"]),
            ]
        ],
        colWidths=[page_w / 3] * 3,
        rowHeights=[40],
    )
    factura_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _BLACK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(factura_tbl)

    firmas = Table(
        [
            [
                Paragraph("Firma Autorizado", styles["meta"]),
                Paragraph("Firma Cliente", styles["meta"]),
                Paragraph("VoBo Bascula", styles["meta"]),
                Paragraph("Firma Calidad", styles["meta"]),
            ]
        ],
        colWidths=[page_w / 4] * 4,
        rowHeights=[55],
    )
    firmas.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _BLACK),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(firmas)

    detalle = ""
    if dev and dev.datos_registro:
        detalle = str(dev.datos_registro.get("detalle_respuesta") or "")
    insp = Table(
        [
            [
                Paragraph(
                    f"<b>Resultado de la inspección:</b><br/>{detalle or ' '}",
                    styles["value"],
                )
            ]
        ],
        colWidths=[page_w],
        rowHeights=[55],
    )
    insp.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, _BLACK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(insp)
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "Nos reservamos el derecho de aceptar la devolución dependiendo de las "
            "condiciones en que sea devuelto el producto",
            styles["disclaimer"],
        )
    )

    doc.build(story)
    return buf.getvalue()


def generar_documento_pqrs_pdf(
    db: Session, pqrs_id: int, *, actor=None
) -> tuple[bytes, str]:
    """PDF único de 2 páginas recreado desde cero: Formato PQRS + Autorización."""
    pqrs_service.get_pqrs_detail(db, pqrs_id, actor=actor)
    pqrs = _load_pqrs(db, pqrs_id)

    writer = PdfWriter()
    for page_pdf in (_build_formato_pqrs(pqrs), _build_autorizacion_devolucion(pqrs)):
        reader = PdfReader(BytesIO(page_pdf))
        writer.add_page(reader.pages[0])

    out = BytesIO()
    writer.write(out)
    return out.getvalue(), f"pqrs-{_radicado(pqrs)}.pdf"
