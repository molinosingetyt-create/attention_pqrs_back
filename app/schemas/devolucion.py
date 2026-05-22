from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pqrs import ProductoPQRSOut


class DevolucionPendienteOut(BaseModel):
    devolucion_id: int
    codigo_devolucion: str | None = None
    pqrs_id: int
    radicado: str
    tipo: str
    estado: str
    cliente_nombre: str
    cliente_apellidos: str
    fecha_cierre: datetime | None
    fecha_registro: datetime
    #: Momento en que quedó radicado el servicio (solo cuando ya no está pendiente).
    fecha_servicio_generado: datetime | None = None
    producto_queja: str | None = None
    area_codigo: str
    area_nombre: str
    inconformidad_nombre: str
    inconformidad_descripcion: str | None
    pendiente: bool
    aplica: bool
    model_config = ConfigDict(from_attributes=True)


class DevolucionRegistroIn(BaseModel):
    """Radicado: el tipo de producto y la fecha del servicio los define el servidor al guardar."""

    responsable: Literal["CLIENTE", "EMPRESA"]
    costo: str | None = Field(None, max_length=120)
    destino: Literal["PRIMERA", "SUBPRODUCTO", "ELIMINACION"]
    cantidad: float = Field(..., gt=0)
    numero_factura: str | None = Field(None, max_length=120)
    lote: str | None = Field(None, max_length=120)
    accion_correctiva: bool
    producto: str = Field(..., min_length=1, max_length=300)
    causa: str = Field(..., min_length=1, max_length=300)
    detalle_respuesta: str = Field(..., min_length=1, max_length=4000)
    comentario_devolucion: str = Field(..., min_length=1, max_length=4000)
    productos_devolucion: list[dict[str, Any]] = Field(default_factory=list)


class DevolucionPQRSResumen(BaseModel):
    id: int
    radicado: str
    tipo: str
    estado: str
    numero_factura: str | None = None
    lote: str | None = None
    descripcion: str | None = None
    fecha_cierre: datetime | None = None
    productos: list[ProductoPQRSOut] = []
    model_config = ConfigDict(from_attributes=True)


class DevolucionDetalleOut(BaseModel):
    id: int
    codigo_devolucion: str | None = None
    pqrs_id: int
    pendiente: bool
    aplica: bool
    observaciones: str | None
    fecha_registro: datetime
    fecha_decision: datetime
    datos_registro: dict[str, Any] | None = None
    cliente_nombre: str
    cliente_apellidos: str
    area_codigo: str
    area_nombre: str
    inconformidad_nombre: str
    inconformidad_descripcion: str | None
    pqrs: DevolucionPQRSResumen
    model_config = ConfigDict(from_attributes=True)
