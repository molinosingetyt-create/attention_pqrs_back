from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RolPermiso(Base):
    """Permiso asignado a un rol (matriz editable desde el backend)."""

    __tablename__ = "rol_permisos"

    rol: Mapped[str] = mapped_column(String(40), primary_key=True)
    permiso: Mapped[str] = mapped_column(String(80), primary_key=True)
