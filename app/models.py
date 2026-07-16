from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# =========================
# USUARIOS
# =========================

class UsuarioCreate(BaseModel):
    nombre: str
    username: str
    rol: str = "usuario"
    permisos: List[str] = []
    activo: bool = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    username: Optional[str] = None
    rol: Optional[str] = None
    permisos: Optional[List[str]] = None
    activo: Optional[bool] = None


# =========================
# INSUMOS
# =========================

class InsumoCreate(BaseModel):
    nombre: str = Field(..., min_length=2)
    descripcion: Optional[str] = None
    unidad_medida: str
    cantidad: float = Field(..., ge=0)
    presentacion: str
    categoria: str
    status: str = "activo"


class InsumoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    unidad_medida: Optional[str] = None
    cantidad: Optional[float] = Field(default=None, ge=0)
    presentacion: Optional[str] = None
    categoria: Optional[str] = None
    status: Optional[str] = None


# =========================
# RECEPCIONES / INGRESO DE STOCK
# =========================

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


# =========================
# PEDIDOS TIPO CARRITO
# =========================

class PedidoItemCreate(BaseModel):
    insumo_id: Optional[int] = None
    nombre: str = Field(..., min_length=2)
    descripcion: Optional[str] = None
    unidad_medida: str
    cantidad: float = Field(..., gt=0)
    presentacion: str
    categoria: str


class PedidoCreate(BaseModel):
    numero_pedido: Optional[str] = None
    observacion: Optional[str] = None
    status: str = "pendiente"
    items: List[PedidoItemCreate]


class PedidoUpdate(BaseModel):
    numero_pedido: Optional[str] = None
    observacion: Optional[str] = None
    status: Optional[str] = None


# =========================
# DESPACHOS TIPO CARRITO
# =========================

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


class TrackingUpdate(BaseModel):
    tracking_estado: str
    tracking_observacion: Optional[str] = None


# =========================
# RESPUESTAS OPCIONALES
# =========================

class DespachoResponse(BaseModel):
    id: int
    codigo_despacho: Optional[str] = None
    entregado_a: Optional[str] = None
    despachado_por: Optional[str] = None
    observacion: Optional[str] = None
    status: str
    qr_token: Optional[str] = None
    qr_activo: Optional[bool] = None
    items: Optional[List[Dict[str, Any]]] = None