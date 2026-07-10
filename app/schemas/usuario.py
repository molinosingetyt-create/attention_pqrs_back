from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import RolUsuario
from app.schemas.common import AppEmailStr


class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    email: AppEmailStr
    rol: RolUsuario
    activo: bool = True


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, max_length=128)


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=120)
    rol: RolUsuario | None = None
    activo: bool | None = None
    password: str | None = Field(None, min_length=6, max_length=128)


class UsuarioOut(UsuarioBase):
    id: int
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)
