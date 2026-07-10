from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Evidencia(Base):
    __tablename__ = "evidencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pqrs_id: Mapped[int] = mapped_column(
        ForeignKey("pqrs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    producto_pqrs_id: Mapped[int | None] = mapped_column(
        ForeignKey("productos_pqrs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    tipo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    titulo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    archivo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    nombre_original: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fecha_subida: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    pqrs = relationship("PQRS", back_populates="evidencias")
    producto_pqrs = relationship("ProductoPQRS", back_populates="evidencias")
