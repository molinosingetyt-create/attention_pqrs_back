from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column("contrasena", String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    pqrs_como_vendedor = relationship(
        "PQRS", back_populates="vendedor", foreign_keys="PQRS.vendedor_id"
    )
    clientes_asignados = relationship(
        "Cliente", back_populates="vendedor_asignado", foreign_keys="Cliente.vendedor_asignado_id"
    )
    seguimientos = relationship("Seguimiento", back_populates="usuario")
