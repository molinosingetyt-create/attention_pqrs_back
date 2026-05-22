from pydantic import BaseModel, ConfigDict, Field


class AreaOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    model_config = ConfigDict(from_attributes=True)


class AreaCreate(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=40)
    nombre: str = Field(..., min_length=2, max_length=120)


class AreaUpdate(BaseModel):
    codigo: str | None = Field(None, min_length=2, max_length=40)
    nombre: str | None = Field(None, min_length=2, max_length=120)
