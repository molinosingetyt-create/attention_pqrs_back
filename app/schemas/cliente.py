from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AppEmailStr


class ClienteBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    apellidos: str | None = Field(None, max_length=120)
    nit: str = Field(..., min_length=3, max_length=40)
    direccion: str | None = Field(None, max_length=200)
    telefono: str | None = Field(None, max_length=40)
    correo: AppEmailStr | None = None
    ciudad: str | None = Field(None, max_length=100)


class ClienteCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    apellidos: str | None = Field(None, max_length=120)
    nit: str = Field(..., min_length=3, max_length=40)
    direccion: str = Field(..., min_length=1, max_length=200)
    telefono: str = Field(..., min_length=1, max_length=40)
    correo: AppEmailStr
    ciudad: str = Field(..., min_length=1, max_length=100)
    vendedor_asignado_id: int | None = Field(
        None,
        description="Vendedor responsable del cliente (misma sede si aplica).",
    )
    sede_id: int | None = Field(
        None,
        description="Sede del cliente. El administrador de sede usa la suya.",
    )


class ClienteUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=120)
    apellidos: str | None = Field(None, max_length=120)
    direccion: str | None = Field(None, max_length=200)
    telefono: str | None = Field(None, max_length=40)
    correo: AppEmailStr | None = None
    ciudad: str | None = Field(None, max_length=100)
    activo: bool | None = Field(
        None, description="Solo administrador: habilitar o deshabilitar el cliente."
    )
    vendedor_asignado_id: int | None = Field(
        None,
        description="Reasignar vendedor responsable.",
    )
    sede_id: int | None = Field(None, description="Reasignar sede del cliente.")


class ClienteOut(ClienteBase):
    id: int
    activo: bool = True
    vendedor_asignado_id: int | None = None
    sede_id: int | None = None
    model_config = ConfigDict(from_attributes=True)
