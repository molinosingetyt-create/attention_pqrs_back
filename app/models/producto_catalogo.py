from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductoCatalogo(Base):
    __tablename__ = "productos_catalogo"
    __table_args__ = (
        UniqueConstraint("categoria_id", "nombre", name="uq_producto_catalogo_cat_nombre"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias_producto.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(250), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    categoria = relationship("CategoriaProducto", back_populates="productos")
    lineas_pqrs = relationship("ProductoPQRS", back_populates="producto_catalogo")
