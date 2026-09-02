"""Alcance de datos por sede.

El administrador global (rol ADMINISTRADOR) ve todas las sedes.
El administrador de sede (ADMINISTRADOR_SEDE) solo opera sobre su sede,
sus clientes y los vendedores asociados a esa sede.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.enums import RolUsuario
from app.models.cliente import Cliente
from app.models.pqrs import PQRS
from app.models.usuario import Usuario


def ve_todas_las_sedes(actor: Usuario | None) -> bool:
    if actor is None:
        return True
    return actor.rol == RolUsuario.ADMINISTRADOR.value


def sede_id_alcance(actor: Usuario | None) -> int | None:
    """ID de sede a filtrar, o None si no hay restricción."""
    if actor is None or ve_todas_las_sedes(actor):
        return None
    if actor.rol == RolUsuario.ADMINISTRADOR_SEDE.value:
        if not actor.sede_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Tu usuario no tiene una sede asignada.",
            )
        return actor.sede_id
    return None


def exigir_sede_activa(db: Session, sede_id: int) -> None:
    from app.models.sede import Sede

    sede = db.get(Sede, sede_id)
    if not sede or not sede.activa:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La sede no existe o está inactiva.",
        )


def vendedor_en_alcance(actor: Usuario | None, vendedor: Usuario) -> bool:
    sid = sede_id_alcance(actor)
    if sid is None:
        return True
    return vendedor.sede_id == sid


def exigir_vendedor_en_alcance(actor: Usuario | None, vendedor: Usuario) -> None:
    if vendedor.rol != RolUsuario.VENDEDOR.value or not vendedor.activo:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "El vendedor no existe o no es un vendedor activo.",
        )
    if not vendedor_en_alcance(actor, vendedor):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Solo puedes asignar vendedores de tu sede.",
        )


def cliente_en_alcance(actor: Usuario | None, cliente: Cliente) -> bool:
    sid = sede_id_alcance(actor)
    if sid is None:
        return True
    if cliente.sede_id == sid:
        return True
    vend = cliente.vendedor_asignado
    return bool(vend and vend.sede_id == sid)


def exigir_cliente_en_alcance(actor: Usuario | None, cliente: Cliente) -> None:
    if not cliente_en_alcance(actor, cliente):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "No tienes permisos sobre este cliente (fuera de tu sede).",
        )


def pqrs_en_alcance(actor: Usuario | None, pqrs: PQRS) -> bool:
    sid = sede_id_alcance(actor)
    if sid is None:
        return True
    if pqrs.cliente and (pqrs.cliente.sede_id == sid):
        return True
    if pqrs.vendedor and pqrs.vendedor.sede_id == sid:
        return True
    return False


def exigir_pqrs_en_alcance(actor: Usuario | None, pqrs: PQRS) -> None:
    if not pqrs_en_alcance(actor, pqrs):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "No tienes permisos sobre esta PQRS (fuera de tu sede).",
        )


def condicion_cliente_por_sede(actor: Usuario | None):
    sid = sede_id_alcance(actor)
    if sid is None:
        return None
    return or_(
        Cliente.sede_id == sid,
        Cliente.vendedor_asignado.has(Usuario.sede_id == sid),
    )


def condicion_pqrs_por_sede(actor: Usuario | None):
    """Usa el join a Cliente y el outerjoin al vendedor (Usuario)."""
    sid = sede_id_alcance(actor)
    if sid is None:
        return None
    return or_(Cliente.sede_id == sid, Usuario.sede_id == sid)
