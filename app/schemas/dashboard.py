from pydantic import BaseModel


class KPIsDashboard(BaseModel):
    total: int
    abiertas: int
    en_proceso: int
    cerradas: int
    rechazadas: int


class ConteoPorTipo(BaseModel):
    tipo: str
    cantidad: int


class ConteoPorArea(BaseModel):
    area_codigo: str
    area_nombre: str
    cantidad: int


class ConteoPorMes(BaseModel):
    mes: str  # YYYY-MM
    cantidad: int


class ConteoPorProductoCategoria(BaseModel):
    categoria: str
    producto: str
    cantidad: int


class DashboardResponse(BaseModel):
    kpis: KPIsDashboard
    por_tipo: list[ConteoPorTipo]
    por_estado: list[ConteoPorTipo]
    por_area: list[ConteoPorArea]
    por_mes: list[ConteoPorMes]
    por_categoria_producto: list[ConteoPorProductoCategoria]
    recientes: list[dict]
