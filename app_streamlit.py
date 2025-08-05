# app_streamlit.py
import streamlit as st
import pandas as pd
import sqlite3
import io
from modelo_tarea import Tarea

DB_NAME = "tareas.db"

# === FUNCIONES BASE DE DATOS ===
def conectar():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = conectar()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
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
    conn.commit()
    conn.close()

def obtener_todas():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM tareas", conn)
    conn.close()
    return df

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
    conn.close()

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

# === INICIALIZACIÓN ===
init_db()
st.set_page_config(page_title="Compromisos OCT", layout="wide")

# === CARGA DE DATOS ===
df_tareas = obtener_todas()
query_params = st.query_params

if 'selected_task' not in st.session_state:
    st.session_state.selected_task = None

# === SIDEBAR ===
st.sidebar.header("Gestión de Tareas")
with st.sidebar.form("form_tarea"):
    if st.session_state.selected_task:
        task = df_tareas[df_tareas['id'] == st.session_state.selected_task].iloc[0]
        nombre = st.text_input("Tarea", value=task['nombre'])
        compromiso = st.text_input("Acciones a realizar", value=task['compromiso'])
        fecha_inicio = st.date_input("Fecha de Inicio", pd.to_datetime(task['fecha_inicio']))
        plazo = st.date_input("Plazo", pd.to_datetime(task['plazo']))
        observaciones = st.text_area("Observaciones", value=task['observaciones'] or "")
        terminado = st.checkbox("Terminada", value=bool(task['terminado']))
        delegada = st.checkbox("Delegada", value=bool(task['delegada']))
    else:
        nombre = st.text_input("Tarea")
        compromiso = st.text_input("Acciones a realizar")
        fecha_inicio = st.date_input("Fecha de Inicio")
        plazo = st.date_input("Plazo")
        observaciones = st.text_area("Observaciones")
        terminado = st.checkbox("Terminada")
        delegada = st.checkbox("Delegada")

    col1, col2 = st.columns(2)
    submitted = col1.form_submit_button("Guardar")
    limpiar = col2.form_submit_button("Limpiar formulario")

    if submitted:
        tarea = Tarea(
            id=st.session_state.selected_task,
            estado="Terminada" if terminado else "Pendiente",
            nombre=nombre,
            compromiso=compromiso,
            terminado=int(terminado),
            delegada=int(delegada),
            fecha_inicio=str(fecha_inicio),
            plazo=str(plazo),
            fecha_realizacion=str(fecha_inicio) if terminado else "",
            observaciones=observaciones
        )
        if st.session_state.selected_task:
            actualizar_tarea(tarea)
            st.success("Tarea actualizada.")
        else:
            agregar_tarea(tarea)
            st.success("Tarea agregada.")
        st.session_state.selected_task = None
        st.rerun()

    if limpiar:
        st.session_state.selected_task = None
        st.rerun()

# === HEADER MÉTRICAS ===
st.title("Compromisos OCT - ISL")
col1, col2 = st.columns(2)
col1.metric("Tareas Completadas", f"{df_tareas['terminado'].sum()} / {len(df_tareas)}")
col2.metric("Tareas Pendientes", f"{len(df_tareas) - df_tareas['terminado'].sum()} / {len(df_tareas)}")

st.progress(df_tareas['terminado'].sum()/len(df_tareas) if len(df_tareas) > 0 else 0.01)

# === EXPORTAR A EXCEL ===
buffer = io.BytesIO()
df_tareas.to_excel(buffer, index=False)
st.download_button(
    label="📥 Exportar a Excel",
    data=buffer.getvalue(),
    file_name="tareas_exportadas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# === LISTADO DE TAREAS ===
st.markdown("---")
st.subheader("Listado de Tareas")

for _, row in df_tareas.iterrows():
    color = "#d4edda" if row['terminado'] else "#f8d7da"
    with st.container():
        st.markdown(f"""
            <div style='background-color:{color};padding:10px;margin-bottom:10px;border-radius:10px;'>
                <strong>{row['nombre']}</strong> - {row['estado']}<br>
                <em>{row['compromiso']}</em><br>
                Plazo: {row['plazo']}, Delegada: {'✅' if row['delegada'] else '❌'}<br>
                Observaciones: {row['observaciones'] or 'Sin observaciones'}<br>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        if col1.button("✏️ Editar", key=f"edit_{row['id']}"):
            st.session_state.selected_task = row['id']
            st.rerun()
        if col2.button("🗑️ Eliminar", key=f"delete_{row['id']}"):
            eliminar_tarea(row['id'])
            st.success("Tarea eliminada.")
            st.rerun()












