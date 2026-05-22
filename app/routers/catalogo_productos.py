from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.categoria_producto import CategoriaProductoOut, ProductoCatalogoOut
from app.services import categoria_producto_service

router = APIRouter(
    prefix="/catalogo-productos",
    tags=["Catálogo de productos"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/categorias", response_model=list[CategoriaProductoOut])
def listar_categorias(
    solo_activos: bool = True,
    db: Session = Depends(get_db),
):
    return categoria_producto_service.list_categorias(db, solo_activos=solo_activos)


@router.get("/productos", response_model=list[ProductoCatalogoOut])
def listar_productos(
    categoria_id: int = Query(..., description="ID de la categoría"),
    solo_activos: bool = True,
    db: Session = Depends(get_db),
):
    return categoria_producto_service.list_productos_por_categoria(
        db, categoria_id, solo_activos=solo_activos
    )
