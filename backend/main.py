
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Base, engine, obtener_db
from models.tarea import Tarea
from ml.estimador import estimar_duracion
from ml.entrenamientos import entrenar_modelo
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AgentFlow API",
    description="Asistente inteligente de productividad",
    version="0.1.0",
    lifespan=lifespan
)


class TareaCrear(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    descripcion: str | None = None
    prioridad: str = "media"
    duracion_estimada: int = Field(default=60, ge=1)


class TareaRespuesta(BaseModel):
    id: int
    titulo: str
    descripcion: str | None
    prioridad: str
    estado: str
    duracion_estimada: int

    model_config = {"from_attributes": True}


@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a AgentFlow"}


@app.get("/salud")
def comprobar_salud():
    return {"estado": "correcto"}


@app.post("/api/tareas", response_model=TareaRespuesta, status_code=201)
def crear_tarea(
    datos: TareaCrear,
    db: Session = Depends(obtener_db)
):
    if datos.prioridad not in ["baja", "media", "alta"]:
        raise HTTPException(
            status_code=422,
            detail="La prioridad debe ser baja, media o alta"
        )

    nueva_tarea = Tarea(**datos.model_dump())
    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)

    return nueva_tarea


@app.get("/api/tareas", response_model=list[TareaRespuesta])
def listar_tareas(db: Session = Depends(obtener_db)):
    return db.query(Tarea).order_by(Tarea.id.desc()).all()


@app.get("/api/tareas/{tarea_id}", response_model=TareaRespuesta)
def obtener_tarea(
    tarea_id: int,
    db: Session = Depends(obtener_db)
):
    tarea = db.get(Tarea, tarea_id)

    if tarea is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    return tarea


@app.patch("/api/tareas/{tarea_id}/completar")
def completar_tarea(
    tarea_id: int,
    db: Session = Depends(obtener_db)
):
    tarea = db.get(Tarea, tarea_id)

    if tarea is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    tarea.estado = "completada"
    db.commit()

    return {"mensaje": "Tarea completada", "id": tarea.id}

@app.put("/api/tareas/{tarea_id}", response_model=TareaRespuesta)
def actualizar_tarea(
    tarea_id: int,
    datos: TareaCrear,
    db: Session = Depends(obtener_db)
):
    tarea = db.get(Tarea, tarea_id)

    if tarea is None:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada"
        )

    tarea.titulo = datos.titulo
    tarea.descripcion = datos.descripcion
    tarea.prioridad = datos.prioridad
    tarea.duracion_estimada = datos.duracion_estimada

    if datos.prioridad not in ["baja", "media", "alta"]:
        raise HTTPException(
            status_code=422,
            detail="La prioridad debe ser baja, media o alta"
        )

    db.commit()
    db.refresh(tarea)

    return tarea

@app.delete("/api/tareas/{tarea_id}")
def eliminar_tarea(
    tarea_id: int,
    db: Session = Depends(obtener_db)
):
    tarea = db.get(Tarea, tarea_id)

    if tarea is None:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada"
        )

    db.delete(tarea)
    db.commit()

    return {
        "mensaje": "Tarea eliminada correctamente",
        "id": tarea_id
    }


class EstimacionSolicitud(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    descripcion: str = ""
    prioridad: str = "media"


@app.post("/api/tareas/estimar-duracion")
def estimar_duracion_tarea(datos: EstimacionSolicitud):
    if datos.prioridad not in ["baja", "media", "alta"]:
        raise HTTPException(
            status_code=422,
            detail="La prioridad debe ser baja, media o alta"
        )

    minutos = estimar_duracion(
        datos.prioridad,
        datos.descripcion
    )

    return {
        "titulo": datos.titulo,
        "prioridad": datos.prioridad,
        "duracion_estimada_minutos": minutos
    }

class RegistrarDuracion(BaseModel):
    duracion_real: int = Field(ge=1, le=10080)


@app.patch("/api/tareas/{tarea_id}/duracion-real")
def registrar_duracion_real(
    tarea_id: int,
    datos: RegistrarDuracion,
    db: Session = Depends(obtener_db)
):
    tarea = db.get(Tarea, tarea_id)

    if tarea is None:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada"
        )

    tarea.duracion_real = datos.duracion_real

    db.commit()
    db.refresh(tarea)

    return {
        "mensaje": "Duración real registrada correctamente",
        "id": tarea.id,
        "duracion_real": tarea.duracion_real
    }

@app.get("/api/estadisticas/duraciones")
def estadisticas_duraciones(
    db: Session = Depends(obtener_db)
):
    tareas = (
        db.query(Tarea)
        .filter(Tarea.duracion_real.isnot(None))
        .all()
    )

    if not tareas:
        return {
            "total_tareas": 0,
            "mensaje": "Aún no hay tareas con duración real registrada",
            "tareas": []
        }

    resultados = []

    for tarea in tareas:
        diferencia = (
            tarea.duracion_real - tarea.duracion_estimada
        )

        resultados.append({
            "id": tarea.id,
            "titulo": tarea.titulo,
            "duracion_estimada": tarea.duracion_estimada,
            "duracion_real": tarea.duracion_real,
            "diferencia_minutos": diferencia
        })

    promedio_estimado = sum(
        t["duracion_estimada"] for t in resultados
    ) / len(resultados)

    promedio_real = sum(
        t["duracion_real"] for t in resultados
    ) / len(resultados)

    error_promedio_absoluto = sum(
        abs(t["diferencia_minutos"]) for t in resultados
    ) / len(resultados)

    return {
        "total_tareas": len(resultados),
        "promedio_estimado_minutos": round(promedio_estimado, 2),
        "promedio_real_minutos": round(promedio_real, 2),
        "error_promedio_absoluto_minutos": round(
            error_promedio_absoluto, 2
        ),
        "tareas": resultados
    }

@app.post("/api/ml/entrenar")
def endpoint_entrenar_modelo():
    resultado = entrenar_modelo()

    if "tareas_disponibles" in resultado:
        raise HTTPException(
            status_code=400,
            detail=resultado
        )

    return resultado

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)