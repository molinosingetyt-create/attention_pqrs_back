from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Inconformidad(Base):
    __tablename__ = "inconformidades"
    __table_args__ = (UniqueConstraint("area_id", "nombre", name="uq_inconformidad_area_nombre"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    area_id: Mapped[int] = mapped_column(
        ForeignKey("areas.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    area = relationship("Area", back_populates="inconformidades")
    pqrs = relationship("PQRS", back_populates="inconformidad")
