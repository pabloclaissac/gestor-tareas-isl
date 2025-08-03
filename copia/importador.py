# importador.py
import pandas as pd
from datetime import datetime
from modelo_tarea import Tarea
import db

def importar_tareas_desde_excel(ruta_excel):
    try:
        df = pd.read_excel(ruta_excel)

        # Limpiamos columnas con espacios
        df.columns = [col.strip().lower() for col in df.columns]

        tareas = []
        for _, fila in df.iterrows():
            # Convertimos la fecha solo a "YYYY-MM-DD"
            fecha_raw = fila.get("fecha")
            if pd.notnull(fecha_raw):
                if isinstance(fecha_raw, datetime):
                    fecha = fecha_raw.date().isoformat()  # solo fecha
                else:
                    fecha = str(fecha_raw).split()[0]
            else:
                fecha = ""

            tarea = Tarea(
                id=None,
                estado=fila.get("estado", ""),
                nombre=fila.get("nombre", ""),
                fecha=fecha,
                avance=fila.get("avance", ""),
                observaciones=fila.get("observaciones", "")
            )
            tareas.append(tarea)

        # Guardamos las tareas
        for t in tareas:
            db.agregar_tarea(t)

        return len(tareas)

    except Exception as e:
        print(f"[ERROR] Falló la importación: {e}")
        return 0
