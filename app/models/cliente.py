from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    apellidos: Mapped[str | None] = mapped_column(String(120), nullable=True)
    nit: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    direccion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    ciudad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    vendedor_asignado_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )

    pqrs = relationship("PQRS", back_populates="cliente")
    vendedor_asignado = relationship(
        "Usuario", foreign_keys=[vendedor_asignado_id], back_populates="clientes_asignados"
    )
