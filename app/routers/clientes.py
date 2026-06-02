from io import BytesIO

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.enums import RolUsuario
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteCreate, ClienteOut, ClienteUpdate
from app.schemas.cliente_carga import ClienteCargaMasivaResultado
from app.schemas.common import Page
from app.services import cliente_carga_masiva_service, cliente_service


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=Page[ClienteOut])
def listar(
    q: str | None = Query(None, description="Buscar por nombre, apellidos, NIT o correo"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    items, total = cliente_service.list_clientes(
        db, q=q, page=page, size=size, actor=actor
    )
    return Page(
        items=[ClienteOut.model_validate(c) for c in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get(
    "/carga-masiva/plantilla",
    dependencies=[Depends(require_roles(RolUsuario.ADMINISTRADOR))],
)
def descargar_plantilla_carga_masiva(db: Session = Depends(get_db)):
    """Plantilla Excel para cargue masivo de clientes (solo administrador)."""
    content = cliente_carga_masiva_service.generar_plantilla_excel(db)
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="plantilla_clientes.xlsx"'
        },
    )


@router.post(
    "/carga-masiva",
    response_model=ClienteCargaMasivaResultado,
    dependencies=[Depends(require_roles(RolUsuario.ADMINISTRADOR))],
)
def importar_carga_masiva(
    archivo: UploadFile = File(..., description="Excel .xlsx con clientes"),
    db: Session = Depends(get_db),
):
    """Importa clientes y asigna vendedor por nombre exacto (solo administrador)."""
    return cliente_carga_masiva_service.importar_clientes_excel(db, archivo)


@router.get("/{cliente_id}", response_model=ClienteOut)
def obtener(
    cliente_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    return cliente_service.get_cliente(db, cliente_id, actor=actor)


@router.post(
    "/",
    response_model=ClienteOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles(
                RolUsuario.ADMINISTRADOR,
                RolUsuario.ADMINISTRATIVO_COMERCIAL,
                RolUsuario.VENDEDOR,
            )
        )
    ],
)
def crear(
    data: ClienteCreate,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    return cliente_service.create_cliente(db, data, actor)


@router.put(
    "/{cliente_id}",
    response_model=ClienteOut,
    dependencies=[
        Depends(
            require_roles(
                RolUsuario.ADMINISTRADOR,
                RolUsuario.ADMINISTRATIVO_COMERCIAL,
                RolUsuario.VENDEDOR,
            )
        )
    ],
)
def actualizar(
    cliente_id: int,
    data: ClienteUpdate,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    return cliente_service.update_cliente(db, cliente_id, data, actor)


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RolUsuario.ADMINISTRADOR))],
)
def eliminar(cliente_id: int, db: Session = Depends(get_db)):
    cliente_service.delete_cliente(db, cliente_id)
