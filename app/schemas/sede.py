from pydantic import BaseModel, ConfigDict, Field


class SedeOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    activa: bool = True
    model_config = ConfigDict(from_attributes=True)


class SedeCreate(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=40)
    nombre: str = Field(..., min_length=2, max_length=120)
    activa: bool = True


class SedeUpdate(BaseModel):
    codigo: str | None = Field(None, min_length=2, max_length=40)
    nombre: str | None = Field(None, min_length=2, max_length=120)
    activa: bool | None = None
