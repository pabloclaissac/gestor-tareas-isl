import streamlit as st
import pandas as pd
import sqlite3
import io

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

def agregar_tarea(tarea):
    conn = conectar()
    c = conn.cursor()
    c.execute('''
        INSERT INTO tareas (
            nombre, compromiso, terminado, delegada,
            fecha_inicio, plazo, fecha_realizacion, observaciones
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', tarea)
    conn.commit()
    conn.close()

def eliminar_tarea(id_tarea):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM tareas WHERE id = ?", (id_tarea,))
    conn.commit()
    conn.close()

def actualizar_tarea(tarea):
    conn = conectar()
    c = conn.cursor()
    c.execute('''
        UPDATE tareas
        SET nombre = ?, compromiso = ?, terminado = ?, delegada = ?,
            fecha_inicio = ?, plazo = ?, fecha_realizacion = ?, observaciones = ?
        WHERE id = ?
    ''', tarea)
    conn.commit()
    conn.close()

# === INICIO APP ===
init_db()
df_tareas = obtener_todas()

st.set_page_config(layout="wide", page_title="Compromisos OCT")
st.markdown("<h1 style='text-align: center; color: #0F69B4;'>Compromisos OCT - ISL</h1>", unsafe_allow_html=True)

# === ÁREA 1: Estadísticas ===
total_tareas = len(df_tareas)
completadas = df_tareas['terminado'].sum() if total_tareas > 0 else 0
pendientes = total_tareas - completadas

col1, col2 = st.columns(2)
col1.metric("Tareas Completadas", f"{int(completadas)} / {total_tareas}")
col2.metric("Tareas Pendientes", f"{int(pendientes)} / {total_tareas}")

st.progress(completadas/total_tareas if total_tareas > 0 else 0.01)

st.markdown("---")

# === ÁREA 2: Formulario + Lista de Tareas ===
col_form, col_lista = st.columns([1, 2], gap="large")

# === FORMULARIO ===
with col_form:
    st.subheader("Ingreso / Edición de Tareas")
    with st.form("form_tarea"):
        nombre = st.text_input("Tarea")
        compromiso = st.text_input("Acciones a realizar")
        fecha_inicio = st.date_input("Fecha de Inicio")
        plazo = st.date_input("Plazo")
        observaciones = st.text_area("Observaciones")
        terminado = st.checkbox("Terminada", False)
        delegada = st.checkbox("Delegada", False)

        submitted = st.form_submit_button("Guardar Tarea")

        if submitted:
            tarea = (
                nombre,
                compromiso,
                int(terminado),
                int(delegada),
                str(fecha_inicio),
                str(plazo),
                str(fecha_inicio) if terminado else "",
                observaciones
            )
            agregar_tarea(tarea)
            st.success("Tarea guardada correctamente.")
            st.experimental_rerun()

    if st.button("📥 Exportar a Excel"):
        buffer = io.BytesIO()
        df_tareas.to_excel(buffer, index=False)
        st.download_button(
            label="Descargar Excel",
            data=buffer.getvalue(),
            file_name="tareas_exportadas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# === LISTADO DE TAREAS ===
with col_lista:
    st.subheader("Listado de Tareas")
    st.dataframe(df_tareas, height=600, use_container_width=True)

    for index, row in df_tareas.iterrows():
        col_edit, col_delete = st.columns([1, 1])
        with col_edit:
            if st.button("✏️ Editar", key=f"editar_{row['id']}"):
                with st.form(f"form_edit_{row['id']}"):
                    nombre = st.text_input("Tarea", value=row['nombre'])
                    compromiso = st.text_input("Acciones", value=row['compromiso'])
                    plazo = st.date_input("Plazo", value=pd.to_datetime(row['plazo']) if row['plazo'] else pd.Timestamp.now())
                    observaciones = st.text_area("Observaciones", value=row['observaciones'] or "")
                    terminado = st.checkbox("Terminada", value=bool(row['terminado']))
                    delegada = st.checkbox("Delegada", value=bool(row['delegada']))
                    submitted_edit = st.form_submit_button("Guardar Cambios")

                    if submitted_edit:
                        tarea = (
                            nombre,
                            compromiso,
                            int(terminado),
                            int(delegada),
                            row['fecha_inicio'],
                            str(plazo),
                            row['fecha_realizacion'],
                            observaciones,
                            row['id']
                        )
                        actualizar_tarea(tarea)
                        st.success("Tarea actualizada.")
                        st.experimental_rerun()
        with col_delete:
            if st.button("🗑️ Eliminar", key=f"eliminar_{row['id']}"):
                eliminar_tarea(row['id'])
                st.warning(f"Tarea {row['nombre']} eliminada.")
                st.experimental_rerun()






