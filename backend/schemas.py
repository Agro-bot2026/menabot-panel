from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ClienteCreate(BaseModel):
    nombre: str
    numero: str
    producto: str
    descripcion: Optional[str] = None
    fecha_vencimiento: datetime


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    numero: Optional[str] = None
    producto: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_vencimiento: Optional[datetime] = None
    activo: Optional[bool] = None


class ClienteResponse(BaseModel):
    id: int
    nombre: str
    numero: str
    producto: str
    descripcion: Optional[str]
    fecha_vencimiento: datetime
    activo: bool
    created_at: datetime
    dias_restantes: Optional[int] = None
    estado: Optional[str] = None  # activo, por_vencer, vencido

    class Config:
        from_attributes = True


class ConfiguracionUpdate(BaseModel):
    dias_notificacion: Optional[str] = None
    mensaje_aviso: Optional[str] = None
    mensaje_vencido: Optional[str] = None
    mensaje_renovar: Optional[str] = None
    hora_envio: Optional[str] = None


class ConfiguracionResponse(BaseModel):
    dias_notificacion: str
    mensaje_aviso: str
    mensaje_vencido: str
    mensaje_renovar: str
    hora_envio: str
    archivo_adjunto: Optional[str]
    tipo_adjunto: Optional[str]

    class Config:
        from_attributes = True


class LogResponse(BaseModel):
    id: int
    cliente_id: int
    numero: str
    tipo: str
    enviado_at: datetime
    exitoso: bool
    error: Optional[str]

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_clientes: int
    activos: int
    por_vencer: int
    vencidos: int
    notificaciones_hoy: int


class BotStatusResponse(BaseModel):
    conectado: bool
    qr: Optional[str] = None
    numero_conectado: Optional[str] = None
