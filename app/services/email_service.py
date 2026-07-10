"""Servicio de notificaciones por correo electrónico (SMTP)."""
from __future__ import annotations

import asyncio
import mimetypes
from pathlib import Path
from typing import Iterable

from email.message import EmailMessage
from email.utils import make_msgid
from html import escape

import aiosmtplib
from loguru import logger

from app.core.config import settings


def _local_path_from_upload_url(url: str) -> Path | None:
    """
    Convierte URLs locales tipo /uploads/... a ruta en disco dentro de UPLOAD_DIR.
    Si la URL no es local, retorna None.
    """
    raw = (url or "").strip()
    if not raw.startswith("/uploads/"):
        return None
    relative = raw.removeprefix("/uploads/").lstrip("/")
    return Path(settings.UPLOAD_DIR) / relative


def _guess_content_type(filename: str, provided: str | None = None) -> tuple[str, str]:
    if provided and "/" in provided:
        maintype, subtype = provided.split("/", 1)
        return maintype, subtype
    guessed, _ = mimetypes.guess_type(filename)
    guessed = guessed or "application/octet-stream"
    maintype, subtype = guessed.split("/", 1)
    return maintype, subtype


async def _send_email(
    to: str,
    subject: str,
    html: str,
    *,
    attachments: Iterable[dict[str, object]] = (),
    inline_related: Iterable[dict[str, object]] = (),
) -> bool:
    if not settings.SMTP_ENABLED:
        logger.info(f"[SMTP DESHABILITADO] Se omite envío a {to}: '{subject}'")
        return False
    if not settings.SMTP_HOST or not to:
        logger.warning("SMTP sin host o destinatario vacío, no se envía correo.")
        return False

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("Este correo requiere un cliente con soporte HTML.")
    msg.add_alternative(html, subtype="html")

    html_part = msg.get_body(preferencelist=("html",))
    if html_part is not None:
        for item in inline_related:
            content = item.get("content")
            filename = str(item.get("filename") or "inline")
            content_type = item.get("content_type")
            cid = str(item.get("cid") or "")
            if not isinstance(content, (bytes, bytearray)) or not cid:
                continue
            maintype, subtype = _guess_content_type(filename, str(content_type) if content_type else None)
            html_part.add_related(
                bytes(content),
                maintype=maintype,
                subtype=subtype,
                cid=cid,
                filename=filename,
            )

    for item in attachments:
        content = item.get("content")
        filename = str(item.get("filename") or "archivo")
        content_type = item.get("content_type")
        if not isinstance(content, (bytes, bytearray)):
            continue
        maintype, subtype = _guess_content_type(filename, str(content_type) if content_type else None)
        msg.add_attachment(bytes(content), maintype=maintype, subtype=subtype, filename=filename)

    try:
        use_tls = settings.SMTP_TLS and settings.SMTP_PORT == 465
        start_tls = settings.SMTP_TLS and not use_tls
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=use_tls,
            start_tls=start_tls,
            timeout=15,
        )
        logger.info(f"Correo enviado a {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Error enviando correo a {to}: {e}")
        return False


def _run(coro) -> None:
    """Lanza una corutina en segundo plano sin bloquear el request."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(coro)
        else:  # pragma: no cover
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)


def _html_value(value: object | None) -> str:
    text = str(value).strip() if value is not None else ""
    return escape(text or "—")


def notify_pqrs_created(to_email: str | None, radicado: str, tipo: str, cliente: str) -> None:
    if not to_email:
        return
    html = f"""
    <h2>Nueva PQRS registrada</h2>
    <p>Se ha registrado una nueva <strong>{tipo}</strong> con el radicado <strong>{radicado}</strong>
    para el cliente <strong>{cliente}</strong>.</p>
    <p>Entraremos en contacto lo antes posible.</p>
    <hr />
    <small>Sistema de gestión PQRS</small>
    """
    _run(_send_email(to_email, f"PQRS {radicado} registrada", html))


def notify_quality_complaint_created(
    *,
    to_emails: list[str],
    area_nombre: str,
    radicado: str,
    tipo: str,
    cliente: str,
    factura: str | None,
    lote: str | None,
    inconformidad: str | None,
    productos: list[str],
    evidencias: list[dict[str, str | None]],
    descripcion: str | None,
    fecha_creacion: object | None,
) -> None:
    recipients = sorted({email.strip().lower() for email in to_emails if email.strip()})
    if not recipients:
        return

    productos_html = "".join(f"<li>{_html_value(producto)}</li>" for producto in productos)
    if not productos_html:
        productos_html = "<li>—</li>"
    # Adjuntos (si existen en disco). Si no, deja el link como respaldo.
    evidencia_items: list[dict[str, str]] = []
    evidencia_attachments: list[dict[str, object]] = []
    preview_cids: list[str] = []
    for idx, evidencia in enumerate(evidencias or []):
        url = (evidencia.get("url") or "").strip()
        if not url:
            continue
        nombre = (evidencia.get("nombre") or "").strip() or url.rsplit("/", 1)[-1]
        content_type = evidencia.get("content_type")

        local_path = _local_path_from_upload_url(url)
        if local_path and local_path.exists() and local_path.is_file():
            try:
                content = local_path.read_bytes()
                evidencia_attachments.append(
                    {"filename": nombre, "content": content, "content_type": content_type}
                )
                evidencia_items.append({"label": nombre, "status": "Adjunto", "url": url})

                # Preview inline para las primeras 3 imágenes (si son imagen/*)
                ctype = str(content_type or "")
                if idx < 3 and ctype.startswith("image/"):
                    cid = make_msgid(domain="pqrs.local")
                    preview_cids.append(cid.strip("<>"))
                else:
                    preview_cids.append("")
            except Exception as e:  # pragma: no cover
                logger.warning(f"No se pudo adjuntar evidencia '{local_path}': {e}")
                evidencia_items.append({"label": nombre, "status": "Link", "url": url})
                preview_cids.append("")
        else:
            evidencia_items.append({"label": nombre, "status": "Link", "url": url})
            preview_cids.append("")

    # Logo corporativo (si existe en backend). Se embebe por CID como imagen relacionada.
    logo_path_candidates = [
        Path(__file__).resolve().parents[1] / "assets" / "logo-la-nieve.svg",
        Path(__file__).resolve().parents[1] / "assets" / "logo-la-nieve.png",
        Path(__file__).resolve().parents[1] / "assets" / "logo-la-nieve.jpg",
        Path(__file__).resolve().parents[1] / "assets" / "logo-la-nieve.jpeg",
    ]
    logo_bytes: bytes | None = None
    logo_filename: str | None = None
    logo_content_type: str | None = None
    for p in logo_path_candidates:
        if p.exists() and p.is_file():
            try:
                logo_bytes = p.read_bytes()
                logo_filename = p.name
                logo_content_type = mimetypes.guess_type(p.name)[0] or "image/svg+xml"
                break
            except Exception:
                pass
    logo_cid = make_msgid(domain="pqrs.local")
    logo_cid_ref = logo_cid.strip("<>")

    evidencias_list_html = ""
    if evidencia_items:
        evidencias_list_html = "".join(
            (
                f"<li style=\"margin:0 0 6px 0;\">"
                f"<strong>{_html_value(item['label'])}</strong> "
                f"<span style=\"color:#6b7280;\">({item['status']})</span>"
                + (
                    f" &nbsp;·&nbsp; <a href=\"{_html_value(item['url'])}\" "
                    f"style=\"color:#0a4874;text-decoration:underline;\">ver</a>"
                    if item["status"] == "Link"
                    else ""
                )
                + "</li>"
            )
            for item in evidencia_items
        )
    else:
        evidencias_list_html = "<li>—</li>"

    preview_html = ""
    # Solo muestra previews si se generó CID (imagen/* y dentro de las primeras 3).
    preview_imgs = [
        f"<img src=\"cid:{cid}\" alt=\"Evidencia\" style=\"max-width:220px;height:auto;border:1px solid #e5e7eb;border-radius:8px;\" />"
        for cid in preview_cids
        if cid
    ]
    if preview_imgs:
        preview_html = (
            "<div style=\"margin-top:8px;display:flex;gap:10px;flex-wrap:wrap;\">"
            + "".join(preview_imgs)
            + "</div>"
        )

    html = f"""
    <div style="background:#f3f4f6;padding:24px 0;">
      <div style="max-width:760px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
        <div style="background:#0a4874;color:#ffffff;padding:18px 22px;display:flex;align-items:center;gap:18px;">
          <!-- Tabla: Outlook y varios clientes ignoran flex para centrar el logo en el óvalo -->
          <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;flex-shrink:0;">
            <tr>
              <td align="center" valign="middle" width="74" height="44" style="width:74px;height:44px;background:#ffffff;border-radius:9999px;text-align:center;vertical-align:middle;padding:0;">
                <img src="cid:{logo_cid_ref}" alt="La Nieve" width="64" height="34" style="display:inline-block;width:64px;height:34px;max-width:64px;object-fit:contain;border:0;vertical-align:middle;" />
              </td>
            </tr>
          </table>
          <div style="padding-top:1px;">
            <div style="font-size:14px;letter-spacing:.08em;text-transform:uppercase;opacity:.9;margin:0 0 2px 0;">Sistema PQRS</div>
            <div style="font-size:18px;font-weight:700;margin:0;line-height:1.25;">Nueva PQRS asignada a {_html_value(area_nombre)}</div>
          </div>
        </div>

        <div style="padding:18px 20px;">
          <p style="margin:0 0 14px 0;color:#111827;">
            Se creó una solicitud que requiere revisión del equipo de <strong>{_html_value(area_nombre)}</strong>.
          </p>

          <table style="border-collapse:collapse;width:100%;font-size:14px;">
            <tr><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:700;width:220px;">Radicado</td><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">{_html_value(radicado)}</td></tr>
            <tr><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:700;">Tipo</td><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">{_html_value(tipo)}</td></tr>
            <tr><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:700;">Cliente</td><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">{_html_value(cliente)}</td></tr>
            <tr><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:700;">Factura</td><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">{_html_value(factura)}</td></tr>
            <tr><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:700;">Lote</td><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">{_html_value(lote)}</td></tr>
            <tr><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:700;">Motivo</td><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">{_html_value(inconformidad)}</td></tr>
            <tr><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:700;">Creación de la solicitud</td><td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">{_html_value(fecha_creacion)}</td></tr>
          </table>

          <div style="margin-top:16px;">
            <div style="font-size:15px;font-weight:800;color:#111827;margin:0 0 6px 0;">Productos</div>
            <ul style="margin:0;padding-left:18px;color:#111827;">{productos_html}</ul>
          </div>

          <div style="margin-top:16px;">
            <div style="font-size:15px;font-weight:800;color:#111827;margin:0 0 6px 0;">Fotos / Evidencias</div>
            <ul style="margin:0;padding-left:18px;color:#111827;">{evidencias_list_html}</ul>
            {preview_html}
          </div>

          <div style="margin-top:16px;">
            <div style="font-size:15px;font-weight:800;color:#111827;margin:0 0 6px 0;">Descripción</div>
            <div style="border-left:4px solid #0a4874;padding:10px 12px;background:#f9fafb;border-radius:8px;color:#111827;">
              {_html_value(descripcion)}
            </div>
          </div>

          <div style="margin-top:18px;color:#6b7280;font-size:12px;border-top:1px solid #e5e7eb;padding-top:12px;">
            Este correo es automático. Sistema de gestión PQRS.
          </div>
        </div>
      </div>
    </div>
    """
    subject = f"PQRS {tipo} · {area_nombre} · {radicado}"
    for email in recipients:
        inline_related: list[dict[str, object]] = []
        if logo_bytes and logo_filename:
            inline_related.append(
                {
                    "filename": logo_filename,
                    "content": logo_bytes,
                    "content_type": logo_content_type or "image/svg+xml",
                    "cid": logo_cid,
                }
            )

        # Relaciona previews de evidencias con CID (solo si se generaron).
        evidence_inline_related: list[dict[str, object]] = []
        for cid, att in zip(preview_cids, evidencia_attachments, strict=False):
            if not cid:
                continue
            content = att.get("content")
            filename = str(att.get("filename") or "evidencia")
            content_type = att.get("content_type") or "application/octet-stream"
            if isinstance(content, (bytes, bytearray)):
                evidence_inline_related.append(
                    {
                        "filename": filename,
                        "content": bytes(content),
                        "content_type": str(content_type),
                        "cid": f"<{cid}>",
                    }
                )

        _run(
            _send_email(
                email,
                subject,
                html,
                attachments=evidencia_attachments,
                inline_related=[*inline_related, *evidence_inline_related],
            )
        )


def notify_pqrs_closed(to_email: str | None, radicado: str, tipo: str, respuesta: str) -> None:
    if not to_email:
        return
    html = f"""
    <h2>PQRS {radicado} cerrada</h2>
    <p>Su <strong>{tipo}</strong> ha sido cerrada con la siguiente respuesta final:</p>
    <blockquote style="border-left:4px solid #1E3A8A;padding:8px 12px;background:#F3F4F6;">
      {respuesta}
    </blockquote>
    <p>Gracias por ayudarnos a mejorar.</p>
    <hr />
    <small>Sistema de gestión PQRS</small>
    """
    _run(_send_email(to_email, f"PQRS {radicado} cerrada", html))
