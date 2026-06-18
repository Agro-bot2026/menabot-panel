from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./menabot.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    numero = Column(String, nullable=False)          # formato: 5491112345678
    producto = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_vencimiento = Column(DateTime, nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Configuracion(Base):
    __tablename__ = "configuracion"
    id = Column(Integer, primary_key=True, index=True)
    # Días de notificación separados por coma: "7,3,1"
    dias_notificacion = Column(String, default="7,3,1")
    # Mensaje personalizable con variables {nombre}, {producto}, {dias}, {fecha}
    mensaje_aviso = Column(Text, default="⚠️ Hola {nombre}, tu {producto} vence en {dias} día(s) el {fecha}.\n\nPara renovar respondé *RENOVAR* o contactate con nosotros.")
    mensaje_vencido = Column(Text, default="🔴 Hola {nombre}, tu {producto} venció el {fecha}.\n\nContactate con nosotros para renovarlo.")
    mensaje_renovar = Column(Text, default="✅ Gracias por tu interés en renovar. En breve un asesor te va a contactar. 🙏")
    # Imagen/archivo adjunto (ruta)
    archivo_adjunto = Column(String, nullable=True)
    tipo_adjunto = Column(String, nullable=True)     # image, document, video
    hora_envio = Column(String, default="09:00")     # hora del cron


class LogNotificacion(Base):
    __tablename__ = "log_notificaciones"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, nullable=False)
    numero = Column(String, nullable=False)
    tipo = Column(String, nullable=False)            # aviso_7, aviso_3, aviso_1, vencido
    enviado_at = Column(DateTime, default=datetime.utcnow)
    exitoso = Column(Boolean, default=True)
    error = Column(Text, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
