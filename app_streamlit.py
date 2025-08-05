# app_streamlit.py
import streamlit as st
import pandas as pd
import sqlite3
from modelo_tarea import Tarea
import io

DB_NAME = "tareas.db"

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
df_tareas = obtener_todas()
total_tareas = len(df_tareas)
completadas = df_tareas['terminado'].sum() if total_tareas > 0 else 0
pendientes = total_tareas - completadas

st.set_page_config(page_title="Compromisos OCT", layout="wide")
st.markdown("<h2 style='text-align:center;'>Compromisos OCT</h2>", unsafe_allow_html=True)

# === HEADER INDICADORES ===
col1, col2 = st.columns(2)
with col1:
    st.metric("Tareas Completadas", f"{int(completadas)} / {total_tareas}")
with col2:
    st.metric("Tareas Pendientes", f"{int(pendientes)} / {total_tareas}")

st.markdown("<hr style='margin:5px;'>", unsafe_allow_html=True)

# === DISEÑO DOS COLUMNAS ===
left_col, right_col = st.columns([1,2], gap="large")

# === FORMULARIO IZQUIERDA ===
with left_col:
    st.subheader("Ingreso / Edición de Tarea")
    if 'modo_edicion' not in st.session_state:
        st.session_state.modo_edicion = False
        st.session_state.tarea_editando = None

    if st.session_state.modo_edicion:
        tarea = st.session_state.tarea_editando
        nombre = st.text_input("Tarea", value=tarea['nombre'])
        compromiso = st.text_input("Acciones a Realizar", value=tarea['compromiso'])
        plazo = st.date_input("Plazo", value=pd.to_datetime(tarea['plazo']))
        observaciones = st.text_area("Observaciones", value=tarea['observaciones'])
        terminado = st.checkbox("Terminada", value=bool(tarea['terminado']))
        delegada = st.checkbox("Delegada", value=bool(tarea['delegada']))

        if st.button("Guardar cambios"):
            tarea_actualizada = Tarea(
                id=tarea['id'],
                estado="Terminada" if terminado else "Pendiente",
                nombre=nombre,
                compromiso=compromiso,
                terminado=int(terminado),
                delegada=int(delegada),
                fecha_inicio=tarea['fecha_inicio'],
                plazo=str(plazo),
                fecha_realizacion=tarea['fecha_realizacion'],
                observaciones=observaciones
            )
            actualizar_tarea(tarea_actualizada)
            st.success("Tarea actualizada correctamente.")
            st.session_state.modo_edicion = False
            st.experimental_rerun()
    else:
        nombre = st.text_input("Tarea")
        compromiso = st.text_input("Acciones a Realizar")
        fecha_inicio = st.date_input("Fecha de Inicio")
        plazo = st.date_input("Plazo")
        observaciones = st.text_area("Observaciones")
        terminado = st.checkbox("Terminada")
        delegada = st.checkbox("Delegada")

        if st.button("Agregar Tarea"):
            tarea = Tarea(
                id=None,
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
            agregar_tarea(tarea)
            st.success("Tarea agregada correctamente.")
            st.experimental_rerun()

# === LISTADO DE TAREAS DERECHA ===
with right_col:
    st.subheader("Listado de Tareas")
    for index, row in df_tareas.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['nombre']}** - {row['estado']}")
            st.caption(f"Plazo: {row['plazo']} | Delegada: {'✅' if row['delegada'] else '❌'} | Terminado: {'✅' if row['terminado'] else '❌'}")
            st.caption(f"Acciones: {row['compromiso']}")
            col1, col2, col3 = st.columns(3)
            if col1.button("Editar", key=f"editar_{row['id']}"):
                st.session_state.modo_edicion = True
                st.session_state.tarea_editando = row
                st.experimental_rerun()
            if col2.button("Eliminar", key=f"eliminar_{row['id']}"):
                eliminar_tarea(row['id'])
                st.experimental_rerun()
            if col3.button("Ver Detalle", key=f"detalle_{row['id']}"):
                st.info(f"Observaciones: {row['observaciones'] or 'Sin observaciones'}")

# === EXPORTAR A EXCEL ===
buffer = io.BytesIO()
df_tareas.to_excel(buffer, index=False)
st.download_button(
    label="Exportar a Excel",
    data=buffer.getvalue(),
    file_name="tareas_exportadas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown("<style>div[data-testid=column] {align-items: flex-start !important;} .stContainer {overflow: auto;} </style>", unsafe_allow_html=True)









