from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Sede(Base):
    """Sede comercial. Usuarios y clientes pueden asociarse a una sede."""

    __tablename__ = "sedes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="sede")
    clientes = relationship("Cliente", back_populates="sede")
