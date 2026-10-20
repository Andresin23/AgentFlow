
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from database import SessionLocal
from models.tarea import Tarea


RUTA_MODELO = Path(__file__).with_name("modelo_duracion.joblib")


def entrenar_modelo():
    db = SessionLocal()

    try:
        tareas = (
            db.query(Tarea)
            .filter(Tarea.duracion_real.isnot(None))
            .all()
        )

        if len(tareas) < 5:
            return {
                "mensaje": "Necesitas al menos 5 tareas con duración real.",
                "tareas_disponibles": len(tareas)
            }

        datos = pd.DataFrame([
            {
                "prioridad": {
                    "baja": 1,
                    "media": 2,
                    "alta": 3
                }.get(t.prioridad.lower(), 2),
                "descripcion_larga": int(
                    len(t.descripcion or "") > 100
                ),
                "duracion_real": t.duracion_real
            }
            for t in tareas
        ])

        X = datos[["prioridad", "descripcion_larga"]]
        y = datos["duracion_real"]

        modelo = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )

        modelo.fit(X, y)

        joblib.dump(modelo, RUTA_MODELO)

        return {
            "mensaje": "Modelo entrenado y guardado correctamente",
            "tareas_utilizadas": len(tareas),
            "archivo": "modelo_duracion.joblib"
        }

    finally:
        db.close()
