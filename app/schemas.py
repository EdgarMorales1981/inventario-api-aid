from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import date



# =========================
# USUARIOS
# =========================

class UsuarioCreate(BaseModel):
    nombre: str
    username: str
    rol: str
    permisos: list[str] = Field(default_factory=list)
    activo: bool = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    username: Optional[str] = None
    rol: Optional[str] = None
    permisos: Optional[list[str]] = None
    activo: Optional[bool] = None


# =========================
# INSUMOS
# =========================

class InsumoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    unidad_medida: str
    presentacion: str
    cantidad: float
    categoria: Literal["medicinas", "aseo_personal", "alimentos"]
    fecha_vencimiento: Optional[date] = None


class InsumoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    unidad_medida: Optional[str] = None
    presentacion: Optional[str] = None
    cantidad: Optional[float] = None
    categoria: Optional[Literal["medicinas", "aseo_personal", "alimentos"]] = None
    fecha_vencimiento: Optional[date] = None
    activo: Optional[bool] = None


# =========================
# RECEPCIONES
# =========================

from pydantic import BaseModel, Field
from typing import Optional


class RecepcionCreate(BaseModel):
    insumo_id: int
    nombre: str
    cantidad: float = Field(..., gt=0)
    presentacion: str
    observacion: Optional[str] = None
    recibido_por: Optional[str] = None
    status: str = "recibido"


class RecepcionUpdate(BaseModel):
    insumo_id: Optional[int] = None
    nombre: Optional[str] = None
    cantidad: Optional[float] = Field(default=None, gt=0)
    presentacion: Optional[str] = None
    observacion: Optional[str] = None
    recibido_por: Optional[str] = None
    status: Optional[str] = None


class DespachoItemCreate(BaseModel):
    insumo_id: int
    cantidad: float = Field(..., gt=0)


class DespachoCreate(BaseModel):
    entregado_a: Optional[str] = None
    despachado_por: Optional[str] = None
    observacion: Optional[str] = None
    items: List[DespachoItemCreate]


class DespachoUpdate(BaseModel):
    entregado_a: Optional[str] = None
    despachado_por: Optional[str] = None
    observacion: Optional[str] = None
    status: Optional[str] = None