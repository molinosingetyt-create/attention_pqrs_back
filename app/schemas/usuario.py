from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import RolUsuario
from app.schemas.common import AppEmailStr
from app.schemas.sede import SedeOut

_ROLES_CON_SEDE_OBLIGATORIA = {RolUsuario.ADMINISTRADOR_SEDE, RolUsuario.VENDEDOR}


def _validar_sede_segun_rol(rol: RolUsuario, sede_id: int | None) -> int | None:
    if rol == RolUsuario.ADMINISTRADOR:
        return None
    if rol in _ROLES_CON_SEDE_OBLIGATORIA and not sede_id:
        raise ValueError(
            "Este perfil debe tener una sede asignada (administrador de sede o vendedor)."
        )
    return sede_id


class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    email: AppEmailStr
    rol: RolUsuario
    activo: bool = True
    sede_id: int | None = None


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, max_length=128)

    @model_validator(mode="after")
    def sede_por_rol(self):
        self.sede_id = _validar_sede_segun_rol(self.rol, self.sede_id)
        return self


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=120)
    rol: RolUsuario | None = None
    activo: bool | None = None
    password: str | None = Field(None, min_length=6, max_length=128)
    sede_id: int | None = None


class UsuarioOut(UsuarioBase):
    id: int
    fecha_creacion: datetime
    sede: SedeOut | None = None

    model_config = ConfigDict(from_attributes=True)
