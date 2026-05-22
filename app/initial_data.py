"""Crea el superusuario inicial y datos semilla de catálogos."""
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import RolUsuario
from app.core.security import hash_password
from app.data.catalogo_productos import CATEGORIAS_CON_PRODUCTOS
from app.models.area import Area
from app.models.categoria_producto import CategoriaProducto
from app.models.inconformidad import Inconformidad
from app.models.producto_catalogo import ProductoCatalogo
from app.models.usuario import Usuario

# (codigo_area, nombre, descripcion_opcional)
CATALOGO_INCONFORMIDADES: list[tuple[str, str, str | None]] = [
    ("CALIDAD", "CALIDAD EMPAQUE", "Empaque, sellado y presentación del producto."),
    ("CALIDAD", "CALIDAD DE PRODUCTO", "Características físicas o organolépticas del producto."),
    ("CALIDAD", "CONTAMINACIÓN FÍSICA", "Cuerpos extraños, materiales o partículas de origen físico."),
    ("CALIDAD", "CONTAMINACIÓN BIOLÓGICA", "Microorganismos, mohos u otros contaminantes de origen biológico."),
    ("CALIDAD", "MAL COLOR", "Color del producto no conforme."),
    ("CALIDAD", "MAL OLOR", "Olor del producto no conforme."),
    ("CALIDAD", "MAL SABOR", "Sabor del producto no conforme."),
    ("CALIDAD", "ROTULADO BOLSA", "Etiquetado o rotulación en bolsa."),
    ("CALIDAD", "CONTENIDO NETO", "Peso o volumen neto declarado."),
    ("LOGISTICA", "TIEMPO DE ENTREGA", "Demoras o incumplimiento en plazos de entrega."),
    ("LOGISTICA", "PRODUCTO NO ENTREGADO", "Faltantes o no entrega del pedido."),
    ("LOGISTICA", "MAL TRATO PERSONAL", "Trato inadecuado por parte del personal."),
    ("COMERCIAL", "MAL ATENCIÓN", "Atención comercial o postventa deficiente."),
]


def _seed_admin(db: Session) -> None:
    exists = db.execute(
        select(Usuario).where(Usuario.email == settings.FIRST_ADMIN_EMAIL.lower())
    ).scalar_one_or_none()
    if exists:
        logger.info("Usuario administrador inicial ya existe, se omite.")
        return

    admin = Usuario(
        nombre=settings.FIRST_ADMIN_NAME,
        email=settings.FIRST_ADMIN_EMAIL.lower(),
        password_hash=hash_password(settings.FIRST_ADMIN_PASSWORD),
        rol=RolUsuario.ADMINISTRADOR.value,
        activo=True,
    )
    db.add(admin)
    db.commit()
    logger.success(f"Administrador creado: {admin.email}")


def _seed_areas(db: Session) -> dict[str, int]:
    """Devuelve mapa codigo -> id de área."""
    rows = list(db.execute(select(Area)).scalars())
    if not rows:
        for codigo, nombre in (
            ("CALIDAD", "CALIDAD"),
            ("LOGISTICA", "LOGISTICA"),
            ("COMERCIAL", "COMERCIAL"),
        ):
            db.add(Area(codigo=codigo, nombre=nombre))
        db.commit()
        rows = list(db.execute(select(Area)).scalars())
    return {a.codigo: a.id for a in rows}


def _seed_inconformidades(db: Session) -> None:
    try:
        areas = _seed_areas(db)
    except Exception as e:
        logger.warning(f"No se pudo sembrar áreas/inconformidades (¿falta migración?): {e}")
        return
    if not areas:
        return
    for codigo, nombre, desc in CATALOGO_INCONFORMIDADES:
        aid = areas.get(codigo)
        if not aid:
            continue
        exists = db.execute(
            select(Inconformidad.id).where(
                Inconformidad.area_id == aid,
                Inconformidad.nombre == nombre,
            )
        ).first()
        if exists:
            continue
        db.add(
            Inconformidad(
                area_id=aid,
                nombre=nombre,
                descripcion=desc,
                activo=True,
            )
        )
    db.commit()


def _seed_catalogo_productos(db: Session) -> None:
    try:
        from sqlalchemy import inspect

        insp = inspect(db.get_bind())
        if not insp.has_table("categorias_producto"):
            return
    except Exception as e:
        logger.warning(f"No se pudo sembrar catálogo de productos: {e}")
        return
    for orden_cat, (cat_nombre, productos) in enumerate(CATEGORIAS_CON_PRODUCTOS):
        cat = db.execute(
            select(CategoriaProducto).where(CategoriaProducto.nombre == cat_nombre)
        ).scalar_one_or_none()
        if not cat:
            cat = CategoriaProducto(nombre=cat_nombre, activo=True, orden=orden_cat)
            db.add(cat)
            db.flush()
        else:
            cat.orden = orden_cat
        for orden_p, nom_p in enumerate(productos):
            ex = db.execute(
                select(ProductoCatalogo.id).where(
                    ProductoCatalogo.categoria_id == cat.id,
                    ProductoCatalogo.nombre == nom_p,
                )
            ).first()
            if ex:
                continue
            db.add(
                ProductoCatalogo(
                    categoria_id=cat.id,
                    nombre=nom_p,
                    activo=True,
                    orden=orden_p,
                )
            )
    db.commit()


def seed() -> None:
    db = SessionLocal()
    try:
        _seed_admin(db)
        _seed_inconformidades(db)
        _seed_catalogo_productos(db)
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover
    seed()
