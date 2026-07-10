from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductoPQRS(Base):
    __tablename__ = "productos_pqrs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pqrs_id: Mapped[int] = mapped_column(
        ForeignKey("pqrs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    producto_catalogo_id: Mapped[int | None] = mapped_column(
        ForeignKey("productos_catalogo.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    inconformidad_id: Mapped[int | None] = mapped_column(
        ForeignKey("inconformidades.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nombre_producto: Mapped[str] = mapped_column(String(250), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=1)
    numero_factura: Mapped[str | None] = mapped_column(String(60), nullable=True)
    lote: Mapped[str | None] = mapped_column(String(60), nullable=True)
    comentario: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    pqrs = relationship("PQRS", back_populates="productos")
    producto_catalogo = relationship("ProductoCatalogo", back_populates="lineas_pqrs")
    inconformidad = relationship("Inconformidad")
    evidencias = relationship(
        "Evidencia",
        back_populates="producto_pqrs",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
