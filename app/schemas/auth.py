from pydantic import BaseModel, Field

from app.schemas.common import AppEmailStr


class LoginRequest(BaseModel):
    email: AppEmailStr
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UsuarioOut"
    permisos: list[str] = []


class SessionOut(BaseModel):
    user: "UsuarioOut"
    permisos: list[str] = []


from app.schemas.usuario import UsuarioOut  # noqa: E402

TokenResponse.model_rebuild()
SessionOut.model_rebuild()
