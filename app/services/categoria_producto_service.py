from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.categoria_producto import CategoriaProducto
from app.models.producto_catalogo import ProductoCatalogo
from app.schemas.categoria_producto import (
    CategoriaProductoCreate,
    CategoriaProductoUpdate,
    ProductoCatalogoCreate,
    ProductoCatalogoUpdate,
)


def list_categorias(db: Session, solo_activos: bool = True) -> list[CategoriaProducto]:
    stmt = select(CategoriaProducto).order_by(CategoriaProducto.orden.asc(), CategoriaProducto.nombre.asc())
    if solo_activos:
        stmt = stmt.where(CategoriaProducto.activo.is_(True))
    return list(db.execute(stmt).scalars())


def list_productos_por_categoria(
    db: Session, categoria_id: int, solo_activos: bool = True
) -> list[ProductoCatalogo]:
    cat = db.get(CategoriaProducto, categoria_id)
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")
    stmt = (
        select(ProductoCatalogo)
        .where(ProductoCatalogo.categoria_id == categoria_id)
        .order_by(ProductoCatalogo.orden.asc(), ProductoCatalogo.nombre.asc())
    )
    if solo_activos:
        stmt = stmt.where(ProductoCatalogo.activo.is_(True))
    return list(db.execute(stmt).scalars())


def create_categoria(db: Session, data: CategoriaProductoCreate) -> CategoriaProducto:
    nombre = data.nombre.strip()
    if db.execute(select(CategoriaProducto.id).where(CategoriaProducto.nombre == nombre)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una categoría con ese nombre.")
    c = CategoriaProducto(nombre=nombre, activo=data.activo, orden=data.orden)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def update_categoria(db: Session, cat_id: int, data: CategoriaProductoUpdate) -> CategoriaProducto:
    c = db.get(CategoriaProducto, cat_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")
    ch = data.model_dump(exclude_unset=True)
    if "nombre" in ch and ch["nombre"] is not None:
        nombre = ch["nombre"].strip()
        exists = db.execute(
            select(CategoriaProducto.id).where(
                CategoriaProducto.nombre == nombre, CategoriaProducto.id != cat_id
            )
        ).first()
        if exists:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una categoría con ese nombre.")
        c.nombre = nombre
    if "activo" in ch and ch["activo"] is not None:
        c.activo = ch["activo"]
    if "orden" in ch and ch["orden"] is not None:
        c.orden = ch["orden"]
    db.commit()
    db.refresh(c)
    return c


def delete_categoria(db: Session, cat_id: int) -> None:
    c = db.get(CategoriaProducto, cat_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")
    db.delete(c)
    db.commit()


def create_producto_catalogo(db: Session, data: ProductoCatalogoCreate) -> ProductoCatalogo:
    if not db.get(CategoriaProducto, data.categoria_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La categoría no existe.")
    nombre = data.nombre.strip()
    exists = db.execute(
        select(ProductoCatalogo.id).where(
            ProductoCatalogo.categoria_id == data.categoria_id,
            ProductoCatalogo.nombre == nombre,
        )
    ).first()
    if exists:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ya existe un producto con ese nombre en la misma categoría.",
        )
    p = ProductoCatalogo(
        categoria_id=data.categoria_id,
        nombre=nombre,
        activo=data.activo,
        orden=data.orden,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def update_producto_catalogo(
    db: Session, producto_id: int, data: ProductoCatalogoUpdate
) -> ProductoCatalogo:
    p = db.get(ProductoCatalogo, producto_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    ch = data.model_dump(exclude_unset=True)
    if "categoria_id" in ch and ch["categoria_id"] is not None:
        if not db.get(CategoriaProducto, ch["categoria_id"]):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La categoría no existe.")
        p.categoria_id = ch["categoria_id"]
    if "nombre" in ch and ch["nombre"] is not None:
        p.nombre = ch["nombre"].strip()
    if "activo" in ch and ch["activo"] is not None:
        p.activo = ch["activo"]
    if "orden" in ch and ch["orden"] is not None:
        p.orden = ch["orden"]
    exists = db.execute(
        select(ProductoCatalogo.id).where(
            ProductoCatalogo.categoria_id == p.categoria_id,
            ProductoCatalogo.nombre == p.nombre,
            ProductoCatalogo.id != producto_id,
        )
    ).first()
    if exists:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ya existe un producto con ese nombre en la misma categoría.",
        )
    db.commit()
    db.refresh(p)
    return p


def delete_producto_catalogo(db: Session, producto_id: int) -> None:
    p = db.get(ProductoCatalogo, producto_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    db.delete(p)
    db.commit()
