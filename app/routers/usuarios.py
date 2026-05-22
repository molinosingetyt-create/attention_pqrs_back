from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.enums import RolUsuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services import usuario_service


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# ---------------------------------------------------------------------------
# Endpoint público-within-app: lista de vendedores para asignar PQRS.
# Accesible a ADMIN, ADMIN_COMERCIAL, CALIDAD y VENDEDOR.
# ---------------------------------------------------------------------------
@router.get(
    "/vendedores",
    response_model=list[UsuarioOut],
    dependencies=[
        Depends(
            require_roles(
                RolUsuario.ADMINISTRADOR,
                RolUsuario.ADMINISTRATIVO_COMERCIAL,
                RolUsuario.CALIDAD,
                RolUsuario.VENDEDOR,
            )
        )
    ],
)
def listar_vendedores(db: Session = Depends(get_db)):
    return usuario_service.list_vendedores(db, solo_activos=True)


# ---------------------------------------------------------------------------
# Resto de endpoints: solo ADMINISTRADOR
# ---------------------------------------------------------------------------
_admin_only = Depends(require_roles(RolUsuario.ADMINISTRADOR))


@router.get("/", response_model=list[UsuarioOut], dependencies=[_admin_only])
def listar(db: Session = Depends(get_db)):
    return usuario_service.list_usuarios(db)


@router.post(
    "/",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_admin_only],
)
def crear(data: UsuarioCreate, db: Session = Depends(get_db)):
    return usuario_service.create_usuario(db, data)


@router.get("/{usuario_id}", response_model=UsuarioOut, dependencies=[_admin_only])
def obtener(usuario_id: int, db: Session = Depends(get_db)):
    return usuario_service.get_usuario(db, usuario_id)


@router.put("/{usuario_id}", response_model=UsuarioOut, dependencies=[_admin_only])
def actualizar(usuario_id: int, data: UsuarioUpdate, db: Session = Depends(get_db)):
    return usuario_service.update_usuario(db, usuario_id, data)


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_admin_only],
)
def desactivar(usuario_id: int, db: Session = Depends(get_db)):
    usuario_service.delete_usuario(db, usuario_id)
