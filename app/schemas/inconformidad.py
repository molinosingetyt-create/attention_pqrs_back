from pydantic import BaseModel, ConfigDict, Field

from app.schemas.area import AreaOut


class InconformidadBase(BaseModel):
    area_id: int
    nombre: str = Field(..., min_length=2, max_length=150)
    descripcion: str | None = Field(None, max_length=2000)
    activo: bool = True


class InconformidadCreate(InconformidadBase):
    pass


class InconformidadUpdate(BaseModel):
    area_id: int | None = None
    nombre: str | None = Field(None, min_length=2, max_length=150)
    descripcion: str | None = Field(None, max_length=2000)
    activo: bool | None = None


class InconformidadOut(InconformidadBase):
    id: int
    area: AreaOut
    model_config = ConfigDict(from_attributes=True)


class InconformidadOutFlat(BaseModel):
    """Lista plana sin anidar área (evita ciclos en algunos usos)."""

    id: int
    area_id: int
    nombre: str
    descripcion: str | None = None
    activo: bool = True
    model_config = ConfigDict(from_attributes=True)
