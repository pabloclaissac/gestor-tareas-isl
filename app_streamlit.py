import streamlit as st
import pandas as pd
import sqlite3
from modelo_tarea import Tarea
import io

DB_NAME = "tareas.db"

# === BASE DE DATOS ===
def conectar():
    return sqlite3.connect(DB_NAME)

def obtener_todas():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM tareas", conn)
    conn.close()
    return df

def actualizar_tarea(tarea: Tarea):
    conn = conectar()
    c = conn.cursor()
    c.execute('''
        UPDATE tareas SET
        estado = ?, nombre = ?, compromiso = ?, terminado = ?, delegada = ?,
        fecha_inicio = ?, plazo = ?, fecha_realizacion = ?, observaciones = ?
        WHERE id = ?
    ''', (
        tarea.estado, tarea.nombre, tarea.compromiso, tarea.terminado, tarea.delegada,
        tarea.fecha_inicio, tarea.plazo, tarea.fecha_realizacion, tarea.observaciones,
        tarea.id
    ))
    conn.commit()
    conn.close()

def eliminar_tarea(id_tarea):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM tareas WHERE id = ?", (id_tarea,))
    conn.commit()
    conn.close()

# === INTERFAZ ===
st.set_page_config(page_title="Gestor Tareas ISL", layout="wide")
st.title("📋 Gestor de Tareas ISL")

# === Query Params ===
params = st.query_params
edit_id = params.get("edit", [None])[0]
delete_id = params.get("delete", [None])[0]

# === DATA ===
df_tareas = obtener_todas()

# === ACCIÓN: ELIMINAR ===
if delete_id:
    eliminar_tarea(delete_id)
    st.query_params.clear()  # Limpia params después de eliminar
    st.success(f"Tarea eliminada correctamente.")

# === LISTADO DE TAREAS ===
st.subheader("Listado de Tareas")

for _, row in df_tareas.iterrows():
    st.markdown(f"### {row['nombre']} - {row['estado']}")
    st.write(f"Acciones: {row['compromiso']}")
    st.write(f"Plazo: {row['plazo']} | Delegada: {'✅' if row['delegada'] else '❌'}")
    
    col1, col2 = st.columns(2)
    if col1.button("✏️ Editar", key=f"edit_{row['id']}"):
        st.query_params["edit"] = row['id']
    if col2.button("🗑️ Eliminar", key=f"delete_{row['id']}"):
        st.query_params["delete"] = row['id']

# === FORMULARIO DE EDICIÓN ===
if edit_id:
    st.markdown("---")
    st.subheader("Editar Tarea")

    tarea_row = df_tareas[df_tareas['id'] == int(edit_id)].iloc[0]

    with st.form("edit_form"):
        nombre = st.text_input("Nombre", value=tarea_row['nombre'])
        compromiso = st.text_input("Compromiso", value=tarea_row['compromiso'])
        plazo = st.date_input("Plazo", value=pd.to_datetime(tarea_row['plazo']))
        observaciones = st.text_area("Observaciones", value=tarea_row['observaciones'] or "")
        terminado = st.checkbox("Terminada", value=bool(tarea_row['terminado']))
        delegada = st.checkbox("Delegada", value=bool(tarea_row['delegada']))

        submitted = st.form_submit_button("Guardar Cambios")
        if submitted:
            tarea = Tarea(
                id=tarea_row['id'],
                estado="Terminada" if terminado else "Pendiente",
                nombre=nombre,
                compromiso=compromiso,
                terminado=int(terminado),
                delegada=int(delegada),
                fecha_inicio=tarea_row['fecha_inicio'],
                plazo=str(plazo),
                fecha_realizacion=tarea_row['fecha_realizacion'],
                observaciones=observaciones
            )
            actualizar_tarea(tarea)
            st.query_params.clear()  # Limpia params después de editar
            st.success("Tarea actualizada correctamente.")




