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
