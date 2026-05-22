from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Devolucion(Base):
    __tablename__ = "devoluciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_devolucion: Mapped[str | None] = mapped_column(
        String(20), nullable=True, unique=True, index=True
    )
    pqrs_id: Mapped[int] = mapped_column(
        ForeignKey("pqrs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    aplica: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    pendiente: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    fecha_decision: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    #: Momento en que se generó el registro de devolución (PQRS cerrada con inconformidad).
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    #: Payload del formulario de radicado (responsable, destino, producto, causa, etc.).
    datos_registro: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    pqrs = relationship("PQRS", back_populates="devolucion")
