from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import aiofiles
import os
import httpx

from database import get_db, init_db, User, Cliente, Configuracion, LogNotificacion
from auth import verify_password, get_password_hash, create_access_token, get_current_user
from schemas import (
    LoginRequest, TokenResponse, ClienteCreate, ClienteUpdate, ClienteResponse,
    ConfiguracionUpdate, ConfiguracionResponse, LogResponse, StatsResponse, BotStatusResponse
)

app = FastAPI(title="MenaBot Panel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

BOT_API_URL = "http://127.0.0.1:3001"  # URL interna del bot Baileys


# ─── INIT ────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_db()
    db = next(get_db())
    # Crear usuario admin por defecto si no existe
    if not db.query(User).first():
        admin = User(username="admin", hashed_password=get_password_hash("admin123"))
        db.add(admin)
        db.commit()
        print("✅ Usuario admin creado: admin / admin123")
    # Crear configuración por defecto si no existe
    if not db.query(Configuracion).first():
        config = Configuracion()
        db.add(config)
        db.commit()
        print("✅ Configuración por defecto creada")
    db.close()


# ─── AUTH ─────────────────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=TokenResponse)
def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/auth/cambiar-usuario")
def cambiar_usuario(
    nuevo_username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existe = db.query(User).filter(User.username == nuevo_username).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ese usuario ya existe")
    current_user.username = nuevo_username
    db.commit()
    return {"message": "Usuario actualizado"}

@app.post("/api/auth/cambiar-password")
def cambiar_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"message": "Contraseña actualizada correctamente"}


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def calcular_estado(fecha_vencimiento: datetime, dias_aviso: list) -> tuple:
    ahora = datetime.utcnow()
    delta = (fecha_vencimiento - ahora).days
    if delta < 0:
        return delta, "vencido"
    elif delta <= max(dias_aviso) if dias_aviso else 7:
        return delta, "por_vencer"
    else:
        return delta, "activo"


# ─── CLIENTES ─────────────────────────────────────────────────────────────────

@app.get("/api/clientes", response_model=List[ClienteResponse])
def listar_clientes(
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Cliente)
    if activo is not None:
        query = query.filter(Cliente.activo == activo)
    clientes = query.order_by(Cliente.fecha_vencimiento.asc()).all()

    config = db.query(Configuracion).first()
    dias_aviso = [int(d) for d in config.dias_notificacion.split(",") if d.strip()] if config else [7, 3, 1]

    result = []
    for c in clientes:
        dias_restantes, estado = calcular_estado(c.fecha_vencimiento, dias_aviso)
        r = ClienteResponse.from_orm(c)
        r.dias_restantes = dias_restantes
        r.estado = estado
        result.append(r)
    return result


@app.post("/api/clientes", response_model=ClienteResponse)
def crear_cliente(
    data: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Normalizar número (quitar + si tiene)
    numero = data.numero.replace("+", "").replace(" ", "")
    cliente = Cliente(
        nombre=data.nombre,
        numero=numero,
        producto=data.producto,
        descripcion=data.descripcion,
        fecha_vencimiento=data.fecha_vencimiento
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    r = ClienteResponse.from_orm(cliente)
    r.dias_restantes = (cliente.fecha_vencimiento - datetime.utcnow()).days
    r.estado = "activo"
    return r


@app.put("/api/clientes/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(
    cliente_id: int,
    data: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for field, value in data.dict(exclude_none=True).items():
        setattr(cliente, field, value)
    cliente.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cliente)
    r = ClienteResponse.from_orm(cliente)
    r.dias_restantes = (cliente.fecha_vencimiento - datetime.utcnow()).days
    r.estado = "activo"
    return r


@app.delete("/api/clientes/{cliente_id}")
def eliminar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(cliente)
    db.commit()
    return {"message": "Cliente eliminado"}


# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

@app.get("/api/configuracion", response_model=ConfiguracionResponse)
def obtener_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(Configuracion).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return config


@app.put("/api/configuracion")
def actualizar_config(
    data: ConfiguracionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(Configuracion).first()
    for field, value in data.dict(exclude_none=True).items():
        setattr(config, field, value)
    db.commit()
    return {"message": "Configuración actualizada"}


@app.post("/api/configuracion/adjunto")
async def subir_adjunto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ext = file.filename.split(".")[-1].lower()
    tipo_map = {
        "jpg": "image", "jpeg": "image", "png": "image", "gif": "image", "webp": "image",
        "pdf": "document", "doc": "document", "docx": "document",
        "mp4": "video", "avi": "video", "mov": "video"
    }
    tipo = tipo_map.get(ext, "document")
    filename = f"adjunto_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)

    config = db.query(Configuracion).first()
    # Eliminar archivo anterior si existe
    if config.archivo_adjunto:
        old_path = os.path.join(UPLOAD_DIR, config.archivo_adjunto.split("/")[-1])
        if os.path.exists(old_path):
            os.remove(old_path)

    config.archivo_adjunto = f"/uploads/{filename}"
    config.tipo_adjunto = tipo
    db.commit()
    return {"archivo": f"/uploads/{filename}", "tipo": tipo}


@app.delete("/api/configuracion/adjunto")
def eliminar_adjunto(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(Configuracion).first()
    if config.archivo_adjunto:
        path = os.path.join(UPLOAD_DIR, config.archivo_adjunto.split("/")[-1])
        if os.path.exists(path):
            os.remove(path)
    config.archivo_adjunto = None
    config.tipo_adjunto = None
    db.commit()
    return {"message": "Adjunto eliminado"}


# ─── ESTADÍSTICAS ─────────────────────────────────────────────────────────────

@app.get("/api/stats", response_model=StatsResponse)
def obtener_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(Configuracion).first()
    dias_aviso = [int(d) for d in config.dias_notificacion.split(",") if d.strip()] if config else [7, 3, 1]
    max_dias = max(dias_aviso) if dias_aviso else 7

    ahora = datetime.utcnow()
    todos = db.query(Cliente).filter(Cliente.activo == True).all()
    vencidos = sum(1 for c in todos if c.fecha_vencimiento < ahora)
    por_vencer = sum(1 for c in todos if ahora <= c.fecha_vencimiento <= ahora + timedelta(days=max_dias))
    activos = sum(1 for c in todos if c.fecha_vencimiento > ahora + timedelta(days=max_dias))

    hoy_inicio = ahora.replace(hour=0, minute=0, second=0)
    notif_hoy = db.query(LogNotificacion).filter(LogNotificacion.enviado_at >= hoy_inicio).count()

    return {
        "total_clientes": len(todos),
        "activos": activos,
        "por_vencer": por_vencer,
        "vencidos": vencidos,
        "notificaciones_hoy": notif_hoy
    }


# ─── LOGS ─────────────────────────────────────────────────────────────────────

@app.get("/api/logs", response_model=List[LogResponse])
def obtener_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(LogNotificacion).order_by(LogNotificacion.enviado_at.desc()).limit(limit).all()


# ─── BOT STATUS ───────────────────────────────────────────────────────────────

@app.get("/api/bot/status", response_model=BotStatusResponse)
async def bot_status(current_user: User = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{BOT_API_URL}/status")
            return r.json()
    except Exception:
        return {"conectado": False, "qr": None, "numero_conectado": None}


@app.post("/api/bot/reiniciar")
async def bot_reiniciar(current_user: User = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(f"{BOT_API_URL}/reiniciar")
            return r.json()
    except Exception:
        return {"message": "No se pudo contactar al bot"}


@app.post("/api/bot/enviar-test")
async def enviar_test(
    numero: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    config = db.query(Configuracion).first()
    mensaje = config.mensaje_aviso.format(
        nombre="Cliente Test",
        producto="Producto Test",
        dias=7,
        fecha="01/01/2025"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{BOT_API_URL}/enviar", json={
                "numero": numero,
                "mensaje": mensaje,
                "archivo": config.archivo_adjunto,
                "tipo": config.tipo_adjunto
            })
            return r.json()
    except Exception as e:
        return {"error": str(e)}


# ─── ENDPOINT INTERNO PARA EL BOT ────────────────────────────────────────────

@app.get("/api/interno/clientes-por-notificar")
def clientes_por_notificar(
    api_key: str,
    db: Session = Depends(get_db)
):
    """Endpoint que consume el bot para saber a quién notificar hoy"""
    if api_key != "menabot-internal-key-2024":
        raise HTTPException(status_code=403, detail="No autorizado")

    config = db.query(Configuracion).first()
    dias_aviso = [int(d) for d in config.dias_notificacion.split(",") if d.strip()]
    ahora = datetime.utcnow()

    resultado = []
    for dias in dias_aviso:
        desde = ahora + timedelta(days=dias) - timedelta(hours=12)
        hasta = ahora + timedelta(days=dias) + timedelta(hours=12)
        clientes = db.query(Cliente).filter(
            Cliente.activo == True,
            Cliente.fecha_vencimiento >= desde,
            Cliente.fecha_vencimiento <= hasta
        ).all()

        for c in clientes:
            # Verificar que no se notificó hoy con el mismo tipo
            tipo = f"aviso_{dias}"
            hoy = ahora.replace(hour=0, minute=0, second=0)
            ya_notificado = db.query(LogNotificacion).filter(
                LogNotificacion.cliente_id == c.id,
                LogNotificacion.tipo == tipo,
                LogNotificacion.enviado_at >= hoy
            ).first()

            if not ya_notificado:
                fecha_str = c.fecha_vencimiento.strftime("%d/%m/%Y")
                mensaje = config.mensaje_aviso.format(
                    nombre=c.nombre,
                    producto=c.producto,
                    dias=dias,
                    fecha=fecha_str
                )
                resultado.append({
                    "cliente_id": c.id,
                    "numero": c.numero,
                    "nombre": c.nombre,
                    "tipo": tipo,
                    "mensaje": mensaje,
                    "archivo": config.archivo_adjunto,
                    "tipo_archivo": config.tipo_adjunto
                })

    # También vencidos hoy
    vencidos = db.query(Cliente).filter(
        Cliente.activo == True,
        Cliente.fecha_vencimiento >= ahora.replace(hour=0, minute=0, second=0),
        Cliente.fecha_vencimiento <= ahora.replace(hour=23, minute=59, second=59)
    ).all()

    for c in vencidos:
        hoy = ahora.replace(hour=0, minute=0, second=0)
        ya_notificado = db.query(LogNotificacion).filter(
            LogNotificacion.cliente_id == c.id,
            LogNotificacion.tipo == "vencido",
            LogNotificacion.enviado_at >= hoy
        ).first()
        if not ya_notificado:
            fecha_str = c.fecha_vencimiento.strftime("%d/%m/%Y")
            mensaje = config.mensaje_vencido.format(
                nombre=c.nombre,
                producto=c.producto,
                fecha=fecha_str
            )
            resultado.append({
                "cliente_id": c.id,
                "numero": c.numero,
                "nombre": c.nombre,
                "tipo": "vencido",
                "mensaje": mensaje,
                "archivo": config.archivo_adjunto,
                "tipo_archivo": config.tipo_adjunto
            })

    return {"notificaciones": resultado, "mensaje_renovar": config.mensaje_renovar}


@app.post("/api/interno/log-notificacion")
def registrar_log(
    cliente_id: int,
    numero: str,
    tipo: str,
    exitoso: bool,
    api_key: str,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if api_key != "menabot-internal-key-2024":
        raise HTTPException(status_code=403, detail="No autorizado")
    log = LogNotificacion(
        cliente_id=cliente_id,
        numero=numero,
        tipo=tipo,
        exitoso=exitoso,
        error=error
    )
    db.add(log)
    db.commit()
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
