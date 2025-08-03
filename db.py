# db.py
import sqlite3
from modelo_tarea import Tarea
import pandas as pd

DB_NAME = "tareas.db"

def conectar():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = conectar()
    c = conn.cursor()
    print("[db] Creando o reparando tabla 'tareas'...")

    # Verificar si existe la tabla
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tareas'")
    if not c.fetchone():
        c.execute('''
            CREATE TABLE tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estado TEXT,
                nombre TEXT,
                compromiso TEXT,
                terminado INTEGER,
                delegada INTEGER,
                fecha_inicio TEXT,
                plazo TEXT,
                fecha_realizacion TEXT,
                observaciones TEXT
            )
        ''')
        print("[db] Tabla 'tareas' creada.")
    else:
        print("[db] Tabla 'tareas' ya existe.")

    conn.commit()
    conn.close()

def agregar_tarea(tarea: Tarea):
    conn = conectar()
    c = conn.cursor()
    c.execute('''
        INSERT INTO tareas (
            estado, nombre, compromiso, terminado, delegada,
            fecha_inicio, plazo, fecha_realizacion, observaciones
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        tarea.estado,
        tarea.nombre,
        tarea.compromiso,
        tarea.terminado,
        tarea.delegada,
        tarea.fecha_inicio,
        tarea.plazo,
        tarea.fecha_realizacion,
        tarea.observaciones
    ))
    conn.commit()

    tarea.id = c.lastrowid  # asigna el ID generado a la instancia
    print(f"[db] Tarea agregada con ID: {tarea.id}")
    conn.close()
    return tarea.id

def obtener_todas():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM tareas")
    filas = c.fetchall()
    conn.close()
    return filas


def eliminar_tarea(id_tarea):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM tareas WHERE id = ?", (id_tarea,))
    conn.commit()
    conn.close()

def actualizar_tarea(tarea: Tarea):
    conn = conectar()
    c = conn.cursor()
    c.execute('''
        UPDATE tareas
        SET estado = ?, nombre = ?, compromiso = ?, terminado = ?, delegada = ?,
            fecha_inicio = ?, plazo = ?, fecha_realizacion = ?, observaciones = ?
        WHERE id = ?
    ''', (
        tarea.estado,
        tarea.nombre,
        tarea.compromiso,
        tarea.terminado,
        tarea.delegada,
        tarea.fecha_inicio,
        tarea.plazo,
        tarea.fecha_realizacion,
        tarea.observaciones,
        tarea.id
    ))
    conn.commit()
    conn.close()
def importar_tareas_desde_excel(ruta_excel):
    df = pd.read_excel(ruta_excel)

    columnas_requeridas = [
        'estado', 'nombre', 'compromiso', 'terminado',
        'delegada', 'fecha_inicio', 'plazo', 'fecha_realizacion', 'observaciones'
    ]
    if not all(col in df.columns for col in columnas_requeridas):
        raise ValueError("El archivo Excel no tiene todas las columnas requeridas.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    for _, fila in df.iterrows():
        c.execute('''
            INSERT INTO tareas (
                estado, nombre, compromiso, terminado, delegada,
                fecha_inicio, plazo, fecha_realizacion, observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fila['estado'], fila['nombre'], fila['compromiso'], fila['terminado'],
            fila['delegada'], fila['fecha_inicio'], fila['plazo'],
            fila['fecha_realizacion'], fila['observaciones']
        ))
    conn.commit()
    conn.close()
