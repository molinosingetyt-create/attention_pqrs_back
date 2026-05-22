"""CRUD de catálogos solo para administrador (pantalla Configuraciones)."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.enums import RolUsuario
from app.schemas.area import AreaCreate, AreaOut, AreaUpdate
from app.schemas.categoria_producto import (
    CategoriaProductoCreate,
    CategoriaProductoOut,
    CategoriaProductoUpdate,
    ProductoCatalogoCreate,
    ProductoCatalogoOut,
    ProductoCatalogoUpdate,
)
from app.services import area_service, categoria_producto_service

router = APIRouter(
    prefix="/configuracion",
    tags=["Configuración"],
    dependencies=[
        Depends(get_current_user),
        Depends(require_roles(RolUsuario.ADMINISTRADOR)),
    ],
)


# --- Áreas ---
@router.get("/areas", response_model=list[AreaOut])
def areas_listar(db: Session = Depends(get_db)):
    return area_service.list_areas(db)


@router.post("/areas", response_model=AreaOut, status_code=status.HTTP_201_CREATED)
def areas_crear(data: AreaCreate, db: Session = Depends(get_db)):
    return area_service.create_area(db, data)


@router.put("/areas/{area_id}", response_model=AreaOut)
def areas_actualizar(area_id: int, data: AreaUpdate, db: Session = Depends(get_db)):
    return area_service.update_area(db, area_id, data)


@router.delete("/areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
def areas_eliminar(area_id: int, db: Session = Depends(get_db)):
    area_service.delete_area(db, area_id)


# --- Categorías de producto ---
@router.get("/categorias-producto", response_model=list[CategoriaProductoOut])
def categorias_listar(
    solo_activos: bool = False,
    db: Session = Depends(get_db),
):
    return categoria_producto_service.list_categorias(db, solo_activos=solo_activos)


@router.post(
    "/categorias-producto",
    response_model=CategoriaProductoOut,
    status_code=status.HTTP_201_CREATED,
)
def categorias_crear(data: CategoriaProductoCreate, db: Session = Depends(get_db)):
    return categoria_producto_service.create_categoria(db, data)


@router.put("/categorias-producto/{cat_id}", response_model=CategoriaProductoOut)
def categorias_actualizar(
    cat_id: int, data: CategoriaProductoUpdate, db: Session = Depends(get_db)
):
    return categoria_producto_service.update_categoria(db, cat_id, data)


@router.delete("/categorias-producto/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
def categorias_eliminar(cat_id: int, db: Session = Depends(get_db)):
    categoria_producto_service.delete_categoria(db, cat_id)


# --- Productos del catálogo ---
@router.get("/productos-catalogo", response_model=list[ProductoCatalogoOut])
def productos_catalogo_listar(
    categoria_id: int = Query(...),
    solo_activos: bool = False,
    db: Session = Depends(get_db),
):
    return categoria_producto_service.list_productos_por_categoria(
        db, categoria_id, solo_activos=solo_activos
    )


@router.post(
    "/productos-catalogo",
    response_model=ProductoCatalogoOut,
    status_code=status.HTTP_201_CREATED,
)
def productos_catalogo_crear(data: ProductoCatalogoCreate, db: Session = Depends(get_db)):
    return categoria_producto_service.create_producto_catalogo(db, data)


@router.put("/productos-catalogo/{prod_id}", response_model=ProductoCatalogoOut)
def productos_catalogo_actualizar(
    prod_id: int, data: ProductoCatalogoUpdate, db: Session = Depends(get_db)
):
    return categoria_producto_service.update_producto_catalogo(db, prod_id, data)


@router.delete("/productos-catalogo/{prod_id}", status_code=status.HTTP_204_NO_CONTENT)
def productos_catalogo_eliminar(prod_id: int, db: Session = Depends(get_db)):
    categoria_producto_service.delete_producto_catalogo(db, prod_id)
