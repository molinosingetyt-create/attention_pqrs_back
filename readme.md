# PQRS API — Backend

API REST para la gestión de **PQRS** (Peticiones, Quejas, Reclamos y Sugerencias). Forma parte del monorepo `attention_pqrs`, junto con el frontend Angular en `attention_pqrs_front/`.

## Descripción general

Sistema orientado a la atención de inconformidades de clientes en procesos comerciales y de calidad. Permite:

- Registrar y dar seguimiento a PQRS con radicado automático.
- Gestionar clientes, vendedores y catálogo de productos por categoría.
- Asociar cada PQRS a un **motivo** (inconformidad) y al **área responsable** (Calidad, Logística, Comercial).
- Subir **evidencias fotográficas por producto** (foto por no conformidad y foto del lote).
- Realizar **análisis y asignación de responsabilidad** (procedente / no procedente).
- Registrar **satisfacción del cliente** al cierre del caso.
- Gestionar **devoluciones** derivadas de PQRS cerradas.
- Consultar un **dashboard** con KPIs, distribución por tipo, área, mes y productos por categoría.
- Control de acceso por **roles** y **permisos** configurables.

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Framework | FastAPI 0.115 |
| Servidor | Uvicorn |
| ORM | SQLAlchemy 2.x |
| Migraciones | Alembic |
| Base de datos | PostgreSQL |
| Autenticación | JWT (python-jose) |
| Contraseñas | bcrypt |
| Validación | Pydantic v2 |
| Archivos | Local o Amazon S3 (boto3) |
| Correo | SMTP (aiosmtplib) |
| Exportación | openpyxl (Excel) |
| Logs | loguru |

## Estructura del proyecto

```
attention_pqrs_back/
├── app/
│   ├── main.py              # Punto de entrada FastAPI
│   ├── initial_data.py      # Datos semilla (admin, áreas, motivos, catálogo)
│   ├── core/                # Config, DB, seguridad, permisos, enums
│   ├── models/              # Modelos SQLAlchemy
│   ├── schemas/             # Esquemas Pydantic (request/response)
│   ├── routers/             # Endpoints HTTP
│   ├── services/            # Lógica de negocio
│   ├── migrations/versions/ # Migraciones Alembic (0001 → 0014)
│   └── uploads/             # Archivos locales (evidencias)
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── .env.example
└── readme.md
```

## Módulos principales

### PQRS
- Creación con uno o más productos del catálogo (factura, lote, comentario).
- Estados: `ABIERTA`, `EN_PROCESO`, `CERRADA`, `RECHAZADA`.
- Tipos: `QUEJA`, `RECLAMO`, `SUGERENCIA`, `PETICION`, `OTRO`.
- Radicado automático: `RAD-000001Q` (sufijo según tipo).
- Evidencias obligatorias por producto: `NO_CONFORMIDAD` y `FOTO_LOTE`.
- Análisis de responsabilidad (solo usuarios del área del motivo).
- Satisfacción del cliente (calificación de atención y expectativas).
- Historial de seguimiento y notificación por correo al área responsable.

### Clientes
- CRUD con campos obligatorios (excepto apellidos).
- Asignación de vendedor y activación/desactivación.
- Carga masiva desde Excel (`.xlsx`).

### Devoluciones
- Se generan automáticamente al cerrar PQRS con motivo asignado.
- Formulario de radicación con datos de producto, causa y destino.

### Dashboard
- KPIs por estado, distribución por tipo y área.
- Gráfico de PQRS por mes (últimos 12 meses).
- Productos por categoría con filtro opcional por rango de fechas.

### Configuración
- Áreas, motivos (inconformidades), categorías y productos de catálogo.
- Matriz de permisos por rol (`PUT /api/permisos/roles/{rol}`).

## Roles de usuario

| Rol | Descripción |
|---|---|
| `ADMINISTRADOR` | Acceso total al sistema |
| `VENDEDOR` | Crea PQRS y gestiona sus clientes asignados |
| `ADMINISTRATIVO_COMERCIAL` | Gestión operativa de PQRS, seguimiento y devoluciones |
| `CALIDAD` | Gestión de devoluciones y motivos del área Calidad |

Los permisos efectivos se almacenan en la tabla `rol_permisos` y pueden modificarse sin redeploy. Si un rol no tiene filas en BD, se usan los valores por defecto definidos en `app/core/permissions.py`.

> **Nota:** El acceso por área en análisis de responsabilidad y devoluciones se valida comparando el `rol` del usuario con el `codigo` del área del motivo (`CALIDAD`, `LOGISTICA`, `COMERCIAL`).

## API

Prefijo base: `/api`

| Recurso | Prefijo |
|---|---|
| Autenticación | `/api/auth` |
| Usuarios | `/api/usuarios` |
| Clientes | `/api/clientes` |
| PQRS | `/api/pqrs` |
| Seguimientos | `/api/seguimientos` |
| Devoluciones | `/api/devoluciones` |
| Dashboard | `/api/dashboard` |
| Motivos | `/api/inconformidades` |
| Catálogo productos | `/api/catalogo-productos` |
| Configuración | `/api/configuracion` |
| Permisos | `/api/permisos` |
| Health check | `/api/health` |

Documentación interactiva:

- Swagger UI: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- ReDoc: [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

### Endpoints destacados de PQRS

```
POST   /api/pqrs/                                    Crear PQRS
GET    /api/pqrs/                                    Listar (filtros + paginación)
GET    /api/pqrs/export                              Exportar a Excel
GET    /api/pqrs/{id}                                Detalle completo
PUT    /api/pqrs/{id}                                Actualizar PQRS
POST   /api/pqrs/{id}/productos                      Agregar productos
POST   /api/pqrs/{id}/evidencias                     Subir foto por producto
PUT    /api/pqrs/{id}/analisis-responsabilidad       Análisis (área responsable)
PUT    /api/pqrs/{id}/satisfaccion-cliente           Encuesta de satisfacción
POST   /api/pqrs/{id}/notificar-calidad               Notificar al área por correo
GET    /api/pqrs/{id}/seguimientos                   Historial de seguimiento
```

## Requisitos previos

- Python 3.12 o 3.13 (recomendado; también compatible con 3.14)
- PostgreSQL 14+
- (Opcional) Docker

> **Python 3.14:** Las versiones anteriores de `pydantic`, `psycopg2-binary` y `sqlalchemy` no tenían soporte completo para 3.14. El `requirements.txt` actual ya incluye versiones compatibles (`pydantic>=2.12`, `psycopg2-binary>=2.9.12`, `sqlalchemy>=2.0.41`). Si usas 3.12/3.13, no necesitas cambios adicionales.

## Configuración local

### 1. Entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 2. Variables de entorno

```bash
cp .env.example .env
```

Variables principales (ver `.env.example` para la lista completa):

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `DATABASE_URL` | Conexión PostgreSQL | `postgresql+psycopg2://pqrs_user:pqrs_pass@localhost:5432/pqrs_db` |
| `SECRET_KEY` | Clave para firmar JWT | *(cambiar en producción)* |
| `CORS_ORIGINS` | Orígenes permitidos del frontend | `http://localhost:4200` |
| `FIRST_ADMIN_EMAIL` | Email del admin inicial | `admin@pqrs.local` |
| `FIRST_ADMIN_PASSWORD` | Contraseña del admin inicial | `Admin123*` |
| `STORAGE_BACKEND` | Almacenamiento de archivos | `local` o `s3` |
| `CALIDAD_EMAILS` | Correos del área Calidad | Separados por coma |
| `SMTP_ENABLED` | Activar envío de correos | `false` |

### 3. Base de datos PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE ROLE pqrs_user WITH LOGIN PASSWORD 'pqrs_pass';
CREATE DATABASE pqrs_db OWNER pqrs_user;
\q
```

Ajusta usuario, contraseña y nombre de BD para que coincidan con `DATABASE_URL` en tu `.env`.

### 4. Iniciar la aplicación

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Al arrancar, la API ejecuta automáticamente:

1. Migraciones Alembic (`upgrade head`).
2. Creación de tablas pendientes.
3. Datos semilla: administrador, áreas, motivos y catálogo de productos.
4. Matriz de permisos por defecto.

### 5. Migraciones manuales (opcional)

```bash
alembic upgrade head          # Aplicar todas las migraciones
alembic current               # Ver revisión actual
alembic history               # Ver historial
```

Migraciones disponibles: `0001` (inicial) → `0014` (satisfacción del cliente).

## Docker

```bash
docker build -t pqrs-api .
docker run -p 8000:8000 --env-file .env pqrs-api
```

El contenedor expone el puerto `8000` e incluye health check en `/api/health`.

## Almacenamiento de archivos

- **Local** (`STORAGE_BACKEND=local`): archivos en `app/uploads/`. Servidos en `/uploads/`.
- **S3** (`STORAGE_BACKEND=s3`): requiere `S3_BUCKET`, `S3_REGION` y credenciales AWS.

Tamaño máximo configurable con `MAX_UPLOAD_MB` (por defecto 10 MB). Las evidencias de producto solo aceptan imágenes.

## Notificaciones por correo

Al notificar una PQRS (`POST /api/pqrs/{id}/notificar-calidad`), se envía un correo a los destinatarios configurados según el área del motivo:

- `CALIDAD_EMAILS`
- `LOGISTICA_EMAILS`
- `COMERCIAL_EMAILS`

Requiere `SMTP_ENABLED=true` y la configuración SMTP correspondiente.

## Formato de código

```bash
pip install black
black app/
```

## Frontend relacionado

El cliente web está en `../attention_pqrs_front/` (Angular + Tailwind + Angular Material). Por defecto consume esta API en `http://localhost:8000/api` con CORS habilitado para `http://localhost:4200`.
