from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import (
    CalificacionAtencion,
    EstadoAnalisisResponsabilidad,
    EstadoPQRS,
    TIPOS_PRODUCTO_MOTIVO_OPCIONALES,
    TipoEvidencia,
    TipoPQRS,
)
from app.schemas.cliente import ClienteOut
from app.schemas.inconformidad import InconformidadOut


class ProductoPQRSBase(BaseModel):
    nombre_producto: str = Field(..., min_length=1, max_length=250)
    cantidad: float = Field(..., gt=0)
    producto_catalogo_id: int | None = None
    numero_factura: str = Field(..., min_length=1, max_length=60)
    lote: str = Field(..., min_length=1, max_length=60)
    comentario: str | None = Field(None, max_length=1000)


class ProductoPQRSCreate(ProductoPQRSBase):
    pass


class ProductoPQRSOut(ProductoPQRSBase):
    id: int
    categoria_nombre: str | None = None
    evidencias: list["EvidenciaOut"] = []
    model_config = ConfigDict(from_attributes=True)


class EvidenciaOut(BaseModel):
    id: int
    producto_pqrs_id: int | None = None
    tipo: TipoEvidencia | None = None
    titulo: str | None = None
    archivo_url: str
    nombre_original: str | None = None
    content_type: str | None = None
    fecha_subida: datetime
    model_config = ConfigDict(from_attributes=True)


class SeguimientoBase(BaseModel):
    estado: EstadoPQRS
    descripcion: str | None = None


class SeguimientoCreate(SeguimientoBase):
    pass


class SeguimientoOut(SeguimientoBase):
    id: int
    usuario_id: int | None = None
    usuario_nombre: str | None = None
    fecha: datetime
    model_config = ConfigDict(from_attributes=True)


class AnalisisResponsabilidadUpsert(BaseModel):
    procedente: bool
    comentario: str = Field(..., min_length=1, max_length=5000)


class AnalisisResponsabilidadOut(BaseModel):
    id: int
    procedente: bool
    comentario: str
    usuario_id: int | None = None
    usuario_nombre: str | None = None
    fecha_actualizacion: datetime
    model_config = ConfigDict(from_attributes=True)


class SatisfaccionClienteUpsert(BaseModel):
    atencion_oportunidad: CalificacionAtencion
    expectativa_cumplida: bool


class SatisfaccionClienteOut(BaseModel):
    id: int
    atencion_oportunidad: CalificacionAtencion
    expectativa_cumplida: bool
    usuario_id: int | None = None
    usuario_nombre: str | None = None
    fecha_actualizacion: datetime
    model_config = ConfigDict(from_attributes=True)


class DevolucionBase(BaseModel):
    aplica: bool
    observaciones: str | None = None


class DevolucionCreate(DevolucionBase):
    pass


class DevolucionOut(DevolucionBase):
    id: int
    fecha_decision: datetime
    pendiente: bool = False
    model_config = ConfigDict(from_attributes=True)


class PQRSBase(BaseModel):
    cliente_id: int
    vendedor_id: int | None = None
    tipo: TipoPQRS
    inconformidad_id: int | None = None
    numero_factura: str | None = Field(None, max_length=60)
    lote: str | None = Field(None, max_length=60)
    descripcion: str | None = None


class PQRSCreate(PQRSBase):
    productos: list[ProductoPQRSCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validar_producto_y_motivo(self):
        opcional = self.tipo in TIPOS_PRODUCTO_MOTIVO_OPCIONALES
        if not opcional and self.inconformidad_id is None:
            raise ValueError("El motivo es obligatorio para este tipo de PQRS.")
        if not opcional and not self.productos:
            raise ValueError("Debe registrar al menos un producto.")
        return self


class PQRSUpdate(BaseModel):
    estado: EstadoPQRS | None = None
    descripcion: str | None = None
    numero_factura: str | None = None
    lote: str | None = None
    inconformidad_id: int | None = None
    vendedor_id: int | None = None


class PQRSListItem(BaseModel):
    id: int
    radicado: str
    tipo: TipoPQRS
    estado: EstadoPQRS
    cliente_id: int
    cliente_nombre: str | None = None
    vendedor_id: int | None = None
    vendedor_nombre: str | None = None
    area_codigo: str | None = None
    area_nombre: str | None = None
    estado_area_responsable: EstadoAnalisisResponsabilidad = (
        EstadoAnalisisResponsabilidad.NO_GESTIONADO
    )
    numero_factura: str | None = None
    fecha_creacion: datetime
    fecha_cierre: datetime | None = None


class PQRSDetail(BaseModel):
    id: int
    radicado: str
    tipo: TipoPQRS
    estado: EstadoPQRS
    numero_factura: str | None = None
    lote: str | None = None
    descripcion: str | None = None
    fecha_creacion: datetime
    fecha_cierre: datetime | None = None

    cliente: ClienteOut
    inconformidad: InconformidadOut | None = None
    vendedor: "UsuarioMini | None" = None

    productos: list[ProductoPQRSOut] = []
    evidencias: list[EvidenciaOut] = []
    seguimientos: list[SeguimientoOut] = []
    analisis_responsabilidad: AnalisisResponsabilidadOut | None = None
    satisfaccion_cliente: SatisfaccionClienteOut | None = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioMini(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    model_config = ConfigDict(from_attributes=True)


PQRSDetail.model_rebuild()
ProductoPQRSOut.model_rebuild()
