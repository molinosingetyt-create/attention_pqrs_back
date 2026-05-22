from pydantic import BaseModel, ConfigDict, Field


class CategoriaProductoOut(BaseModel):
    id: int
    nombre: str
    activo: bool
    orden: int
    model_config = ConfigDict(from_attributes=True)


class CategoriaProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150)
    activo: bool = True
    orden: int = 0


class CategoriaProductoUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=150)
    activo: bool | None = None
    orden: int | None = None


class ProductoCatalogoOut(BaseModel):
    id: int
    categoria_id: int
    nombre: str
    activo: bool
    orden: int
    model_config = ConfigDict(from_attributes=True)


class ProductoCatalogoCreate(BaseModel):
    categoria_id: int
    nombre: str = Field(..., min_length=1, max_length=250)
    activo: bool = True
    orden: int = 0


class ProductoCatalogoUpdate(BaseModel):
    categoria_id: int | None = None
    nombre: str | None = Field(None, min_length=1, max_length=250)
    activo: bool | None = None
    orden: int | None = None
