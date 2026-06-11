from pydantic import BaseModel, Field


class PermisoCatalogoOut(BaseModel):
    codigo: str
    modulo: str
    descripcion: str


class RolPermisosOut(BaseModel):
    rol: str
    permisos: list[str]


class MatrizPermisosOut(BaseModel):
    roles: list[RolPermisosOut]


class RolPermisosUpdate(BaseModel):
    permisos: list[str] = Field(..., description="Lista completa de códigos de permiso para el rol")
