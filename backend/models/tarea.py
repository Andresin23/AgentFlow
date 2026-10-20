
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy import Boolean
from sqlalchemy.sql import func

from database import Base


class Tarea(Base):
    __tablename__ = "tareas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    prioridad = Column(String(20), default="media")
    estado = Column(String(20), default="pendiente")
    fecha_limite = Column(DateTime, nullable=True)
    duracion_estimada = Column(Integer, default=60)
    duracion_real = Column(Integer, nullable=True)
    creada_en = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
