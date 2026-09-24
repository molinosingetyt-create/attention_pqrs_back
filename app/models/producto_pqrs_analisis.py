from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductoPqrsAnalisis(Base):
    """Concepto de procedencia y observación para un producto de la PQRS.

    Reemplaza al análisis único por radicado (`PqrsAnalisisResponsabilidad`),
    que queda solo como histórico de lectura: un mismo radicado puede resultar
    procedente para un producto y no procedente para otro.
    """

    __tablename__ = "producto_pqrs_analisis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    producto_pqrs_id: Mapped[int] = mapped_column(
        ForeignKey("productos_pqrs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    procedente: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comentario: Mapped[str] = mapped_column(Text, nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    producto = relationship("ProductoPQRS", back_populates="analisis")
    usuario = relationship("Usuario")
