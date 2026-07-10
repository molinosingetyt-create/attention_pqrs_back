from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PqrsSatisfaccionCliente(Base):
    __tablename__ = "pqrs_satisfaccion_cliente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pqrs_id: Mapped[int] = mapped_column(
        ForeignKey("pqrs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    atencion_oportunidad: Mapped[str] = mapped_column(String(20), nullable=False)
    expectativa_cumplida: Mapped[bool] = mapped_column(Boolean, nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    pqrs = relationship("PQRS", back_populates="satisfaccion_cliente")
    usuario = relationship("Usuario")
