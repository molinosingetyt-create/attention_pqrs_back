"""Schemas genéricos: paginación y respuestas comunes."""
import re
from typing import Annotated, Generic, TypeVar

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, Field

T = TypeVar("T")

_INTERNAL_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
    r"\.(?:local|localhost|test|invalid|internal)$",
    re.IGNORECASE,
)


def normalize_app_email(value: str) -> str:
    """Valida correos públicos y permite dominios internos de desarrollo (.local, etc.)."""
    normalized = value.strip().lower()
    try:
        return validate_email(normalized, check_deliverability=False).normalized
    except EmailNotValidError:
        if _INTERNAL_EMAIL_RE.match(normalized):
            return normalized
        raise ValueError("value is not a valid email address") from None


AppEmailStr = Annotated[str, AfterValidator(normalize_app_email)]


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1, le=200)
    pages: int = Field(..., ge=0)


class Message(BaseModel):
    detail: str
