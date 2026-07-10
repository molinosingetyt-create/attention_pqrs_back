from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PQRS(Base):
    __tablename__ = "pqrs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    vendedor_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    inconformidad_id: Mapped[int | None] = mapped_column(
        ForeignKey("inconformidades.id", ondelete="SET NULL"), nullable=True, index=True
    )

    tipo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ABIERTA", index=True
    )
    numero_factura: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    radicado: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True, index=True)
    lote: Mapped[str | None] = mapped_column(String(60), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    fecha_cierre: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    cliente = relationship("Cliente", back_populates="pqrs")
    vendedor = relationship(
        "Usuario", back_populates="pqrs_como_vendedor", foreign_keys=[vendedor_id]
    )
    inconformidad = relationship("Inconformidad", back_populates="pqrs")
    productos = relationship(
        "ProductoPQRS",
        back_populates="pqrs",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    evidencias = relationship(
        "Evidencia",
        back_populates="pqrs",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    seguimientos = relationship(
        "Seguimiento",
        back_populates="pqrs",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Seguimiento.fecha.desc()",
    )
    devolucion = relationship(
        "Devolucion",
        back_populates="pqrs",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    analisis_responsabilidad = relationship(
        "PqrsAnalisisResponsabilidad",
        back_populates="pqrs",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    satisfaccion_cliente = relationship(
        "PqrsSatisfaccionCliente",
        back_populates="pqrs",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
