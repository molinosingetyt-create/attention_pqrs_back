from pydantic import BaseModel, Field


class FilaCargaClienteResultado(BaseModel):
    fila: int
    nit: str | None = None
    exito: bool
    mensaje: str
    cliente_id: int | None = None


class ClienteCargaMasivaResultado(BaseModel):
    total_filas: int
    creados: int
    errores: int
    filas: list[FilaCargaClienteResultado] = Field(default_factory=list)
