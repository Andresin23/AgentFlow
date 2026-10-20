
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


RUTA_MODELO = Path(__file__).with_name("modelo_duracion.joblib")


# Modelo inicial de respaldo para cuando aún no hay uno guardado
datos = pd.DataFrame({
    "prioridad": [1, 1, 2, 2, 3, 3, 1, 2, 3, 1],
    "descripcion_larga": [0, 1, 0, 1, 0, 1, 1, 0, 1, 0],
    "duracion_minutos": [20, 45, 30, 60, 40, 90, 50, 35, 80, 25]
})

X = datos[["prioridad", "descripcion_larga"]]
y = datos["duracion_minutos"]

modelo_inicial = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)
modelo_inicial.fit(X, y)


def estimar_duracion(prioridad: str, descripcion: str = "") -> int:
    prioridades = {"baja": 1, "media": 2, "alta": 3}

    valor_prioridad = prioridades.get(prioridad.lower(), 2)
    descripcion_larga = int(len(descripcion) > 100)

    entrada = pd.DataFrame([{
        "prioridad": valor_prioridad,
        "descripcion_larga": descripcion_larga
    }])

    if RUTA_MODELO.exists():
        modelo = joblib.load(RUTA_MODELO)
    else:
        modelo = modelo_inicial

    estimacion = modelo.predict(entrada)[0]

    return max(5, round(estimacion))
