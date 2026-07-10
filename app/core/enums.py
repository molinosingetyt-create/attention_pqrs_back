"""Enums del dominio PQRS."""
from enum import Enum


class RolUsuario(str, Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    VENDEDOR = "VENDEDOR"
    ADMINISTRATIVO_COMERCIAL = "ADMINISTRATIVO_COMERCIAL"
    CALIDAD = "CALIDAD"


class TipoPQRS(str, Enum):
    QUEJA = "QUEJA"
    RECLAMO = "RECLAMO"
    SUGERENCIA = "SUGERENCIA"
    PETICION = "PETICION"
    OTRO = "OTRO"


class EstadoPQRS(str, Enum):
    ABIERTA = "ABIERTA"
    EN_PROCESO = "EN_PROCESO"
    CERRADA = "CERRADA"
    RECHAZADA = "RECHAZADA"


class EstadoAnalisisResponsabilidad(str, Enum):
    NO_GESTIONADO = "NO GESTIONADO"
    PROCEDENTE = "PROCEDENTE"
    NO_PROCEDENTE = "NO PROCEDENTE"


class TipoEvidencia(str, Enum):
    NO_CONFORMIDAD = "NO_CONFORMIDAD"
    FOTO_LOTE = "FOTO_LOTE"


TIPOS_EVIDENCIA_REQUERIDOS: frozenset[TipoEvidencia] = frozenset(
    {TipoEvidencia.NO_CONFORMIDAD, TipoEvidencia.FOTO_LOTE}
)

TIPOS_EVIDENCIA_LABELS: dict[TipoEvidencia, str] = {
    TipoEvidencia.NO_CONFORMIDAD: "Por no conformidad",
    TipoEvidencia.FOTO_LOTE: "Foto del lote",
}


class CalificacionAtencion(str, Enum):
    EXCELENTE = "EXCELENTE"
    BUENA = "BUENA"
    REGULAR = "REGULAR"
    MALA = "MALA"


CALIFICACION_ATENCION_LABELS: dict[CalificacionAtencion, str] = {
    CalificacionAtencion.EXCELENTE: "Excelente",
    CalificacionAtencion.BUENA: "Buena",
    CalificacionAtencion.REGULAR: "Regular",
    CalificacionAtencion.MALA: "Mala",
}
