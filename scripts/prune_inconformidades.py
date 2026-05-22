"""
Elimina inconformidades que no están en el catálogo oficial (initial_data.CATALOGO_INCONFORMIDADES).

Las PQRS que apuntaban a una fila borrada quedan con inconformidad_id = NULL (ON DELETE SET NULL).

Uso (desde la carpeta backend, con DATABASE_URL / .env cargado):

  cd backend && python scripts/prune_inconformidades.py

Docker:

  docker compose exec backend python scripts/prune_inconformidades.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.initial_data import CATALOGO_INCONFORMIDADES
from app.models.area import Area
from app.models.inconformidad import Inconformidad


def main() -> None:
    db = SessionLocal()
    try:
        areas = {a.codigo: a.id for a in db.execute(select(Area)).scalars()}
        allowed: set[tuple[int, str]] = set()
        for codigo, nombre, _desc in CATALOGO_INCONFORMIDADES:
            aid = areas.get(codigo)
            if aid is not None:
                allowed.add((aid, nombre))

        inconformidades = list(db.execute(select(Inconformidad)).scalars())
        to_delete = [
            i
            for i in inconformidades
            if i.area_id is None or (i.area_id, i.nombre) not in allowed
        ]
        for row in to_delete:
            db.delete(row)
        db.commit()
        print(f"Catálogo permitido: {len(allowed)} inconformidades.")
        print(f"Eliminadas: {len(to_delete)} filas (antiguas o fuera de catálogo).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
