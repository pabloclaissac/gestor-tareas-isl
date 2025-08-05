import streamlit as st
import pandas as pd
import sqlite3
import io

DB_NAME = "tareas.db"

# === BASE DE DATOS ===
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
            plazo TEXT,
            observaciones TEXT,
            terminado INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# === CRUD ===
def obtener_tareas():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM tareas", conn)
    conn.close()
    return df

def agregar_tarea(nombre, compromiso, plazo, observaciones):
    conn = conectar()
    c = conn.cursor()
    c.execute('''INSERT INTO tareas (nombre, compromiso, plazo, observaciones, terminado) VALUES (?, ?, ?, ?, 0)''',
              (nombre, compromiso, plazo, observaciones))
    conn.commit()
    conn.close()

def actualizar_tarea(id_tarea, nombre, compromiso, plazo, observaciones, terminado):
    conn = conectar()
    c = conn.cursor()
    c.execute('''
        UPDATE tareas SET nombre = ?, compromiso = ?, plazo = ?, observaciones = ?, terminado = ? WHERE id = ?
    ''', (nombre, compromiso, plazo, observaciones, terminado, id_tarea))
    conn.commit()
    conn.close()

def eliminar_tarea(id_tarea):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM tareas WHERE id = ?", (id_tarea,))
    conn.commit()
    conn.close()

# === INICIO ===
init_db()
st.set_page_config(layout="wide", page_title="Gestor Tareas ISL")
st.title("Gestor de Tareas ISL")

# === LAYOUT ===
col_form, col_tareas = st.columns([1, 2], gap="large")

# === FORMULARIO ===
with col_form:
    st.subheader("Nueva Tarea")
    nombre = st.text_input("Tarea")
    compromiso = st.text_input("Acciones a realizar")
    plazo = st.date_input("Plazo")
    observaciones = st.text_area("Observaciones")

    col1, col2 = st.columns(2)
    if col1.button("Guardar Tarea"):
        if nombre.strip() != "":
            agregar_tarea(nombre, compromiso, str(plazo), observaciones)
            st.success("Tarea guardada correctamente.")
            st.experimental_rerun()
        else:
            st.warning("Debe ingresar un nombre de tarea.")
    if col2.button("Limpiar Formulario"):
        st.experimental_rerun()

# === EXPORTAR ===
df = obtener_tareas()
if not df.empty:
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button("📥 Exportar a Excel", data=buffer.getvalue(), file_name="tareas_exportadas.xlsx")

# === LISTADO DE TAREAS ===
with col_tareas:
    st.subheader("Tareas Registradas")
    if df.empty:
        st.info("No hay tareas registradas.")
    else:
        for idx, row in df.iterrows():
            with st.container(border=True):
                st.markdown(f"#### {row['nombre']}")
                st.markdown(f"**Acciones:** {row['compromiso']}")
                st.markdown(f"**Plazo:** {row['plazo']}")
                st.markdown(f"**Observaciones:** {row['observaciones'] or 'Sin observaciones'}")
                terminado = st.checkbox("Terminada", value=bool(row['terminado']), key=f"chk_{row['id']}")

                with st.expander("Editar Tarea"):
                    new_nombre = st.text_input("Tarea", value=row['nombre'], key=f"edit_nombre_{row['id']}")
                    new_compromiso = st.text_input("Acciones", value=row['compromiso'], key=f"edit_compromiso_{row['id']}")
                    new_plazo = st.date_input("Plazo", value=pd.to_datetime(row['plazo']), key=f"edit_plazo_{row['id']}")
                    new_observaciones = st.text_area("Observaciones", value=row['observaciones'], key=f"edit_obs_{row['id']}")

                    if st.button("Guardar Cambios", key=f"btn_guardar_{row['id']}"):
                        actualizar_tarea(row['id'], new_nombre, new_compromiso, str(new_plazo), new_observaciones, int(terminado))
                        st.success("Tarea actualizada.")
                        st.experimental_rerun()

                if st.button("🗑️ Eliminar", key=f"btn_eliminar_{row['id']}"):
                    eliminar_tarea(row['id'])
                    st.warning("Tarea eliminada.")
                    st.experimental_rerun()






