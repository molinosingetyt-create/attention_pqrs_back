"""Servicio de almacenamiento de archivos. Soporta backend local y S3."""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from loguru import logger

from app.core.config import settings


@dataclass
class StoredFile:
    url: str
    original_name: str
    content_type: str | None
    size: int


ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".txt", ".csv", ".zip",
}


def _validate(file: UploadFile, size: int) -> None:
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"El archivo supera el tamaño máximo de {settings.MAX_UPLOAD_MB} MB.",
        )
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Extensión '{ext}' no permitida.",
        )


async def save_upload(file: UploadFile, folder: str = "evidencias") -> StoredFile:
    content = await file.read()
    size = len(content)
    _validate(file, size)

    safe_name = f"{uuid.uuid4().hex}{Path(file.filename or '').suffix.lower()}"

    if settings.STORAGE_BACKEND == "s3":
        return _save_s3(content, safe_name, file, folder, size)
    return _save_local(content, safe_name, file, folder, size)


def _save_local(content: bytes, safe_name: str, file: UploadFile, folder: str, size: int) -> StoredFile:
    base = Path(settings.UPLOAD_DIR) / folder
    base.mkdir(parents=True, exist_ok=True)
    path = base / safe_name
    with open(path, "wb") as f:
        f.write(content)
    logger.info(f"Archivo guardado en local: {path}")
    relative = f"/uploads/{folder}/{safe_name}"
    return StoredFile(
        url=relative,
        original_name=file.filename or safe_name,
        content_type=file.content_type,
        size=size,
    )


def _save_s3(content: bytes, safe_name: str, file: UploadFile, folder: str, size: int) -> StoredFile:
    try:
        import boto3
    except ImportError as e:  # pragma: no cover
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"boto3 no disponible: {e}")

    if not settings.S3_BUCKET:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "S3_BUCKET no configurado.")

    s3 = boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )
    key = f"{folder}/{safe_name}"
    s3.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=content,
        ContentType=file.content_type or "application/octet-stream",
    )
    url = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{key}"
    logger.info(f"Archivo subido a S3: {url}")
    return StoredFile(
        url=url,
        original_name=file.filename or safe_name,
        content_type=file.content_type,
        size=size,
    )


def ensure_upload_dirs() -> None:
    if settings.STORAGE_BACKEND == "local":
        os.makedirs(Path(settings.UPLOAD_DIR) / "evidencias", exist_ok=True)
