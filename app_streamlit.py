import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

DB_NAME = "tareas.db"

# ---------------- DB ----------------
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estado TEXT,
                nombre TEXT,
                responsable TEXT,
                avance TEXT,
                observaciones TEXT,
                fecha_inicio TEXT,
                fecha_termino TEXT
            )
        """)

def obtener_tareas():
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query("SELECT * FROM tareas ORDER BY id", conn)

def agregar_tarea(datos):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO tareas (estado, nombre, responsable, avance, observaciones, fecha_inicio, fecha_termino)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, datos)
        conn.commit()

def actualizar_tarea(tarea_id, datos):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            UPDATE tareas
            SET estado=?, nombre=?, responsable=?, avance=?, observaciones=?, fecha_inicio=?, fecha_termino=?
            WHERE id=?
        """, (*datos, tarea_id))
        conn.commit()

def eliminar_tarea(tarea_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM tareas WHERE id=?", (tarea_id,))
        conn.commit()

# ---------------- UI ----------------
def main():
    st.set_page_config(layout="wide", page_title="Gestor de Tareas")
    st.title("Gestor de Tareas")

    init_db()
    df = obtener_tareas()

    # session state para mantener selección y modo
    if "selected_id" not in st.session_state:
        st.session_state.selected_id = None
    if "modo_edicion" not in st.session_state:
        st.session_state.modo_edicion = False

    col_left, col_right = st.columns([1, 2])

    # ---------- Formulario (izquierda) ----------
    with col_left:
        st.subheader("Agregar / Editar Tarea")

        # Campos del formulario
        estado = st.selectbox("Estado", ["Pendiente", "En Proceso", "Completada"])
        nombre = st.text_input("Nombre de Tarea")
        responsable = st.text_input("Responsable")
        avance = st.text_input("Avance")
        observaciones = st.text_area("Observaciones")
        fecha_inicio = st.date_input("Fecha de Inicio", value=date.today())
        fecha_termino = st.date_input("Fecha de Término", value=date.today())

        # Si hay una tarea seleccionada, cargamos sus valores en el formulario al mostrarse
        if st.session_state.selected_id is not None and not st.session_state.modo_edicion:
            # cargar datos en el formulario (solo una vez)
            sel = df[df["id"] == st.session_state.selected_id]
            if not sel.empty:
                r = sel.iloc[0]
                # Asignar valores (usa experimental_set_query_params para evitar re-rendering problemático)
                # pero aquí los seteamos directamente a st.session_state para mantenerlos visibles:
                st.session_state["__auto_loaded_estado"] = r["estado"]
                st.session_state["__auto_loaded_nombre"] = r["nombre"]
                st.session_state["__auto_loaded_responsable"] = r["responsable"]
                st.session_state["__auto_loaded_avance"] = r["avance"]
                st.session_state["__auto_loaded_observaciones"] = r["observaciones"] or ""
                st.session_state["__auto_loaded_fecha_inicio"] = pd.to_datetime(r["fecha_inicio"]).date() if r["fecha_inicio"] else date.today()
                st.session_state["__auto_loaded_fecha_termino"] = pd.to_datetime(r["fecha_termino"]).date() if r["fecha_termino"] else date.today()
                st.session_state.modo_edicion = True

        # Aplicar valores automáticos si existen (sobre-escritura de inputs)
        # Nota: los siguientes widgets recogen valores iniciales desde session_state si existen
        estado = st.selectbox("Estado (cargado)", ["Pendiente", "En Proceso", "Completada"],
                              index=(["Pendiente","En Proceso","Completada"].index(st.session_state.get("__auto_loaded_estado")) 
                                     if "__auto_loaded_estado" in st.session_state else 0))
        nombre = st.text_input("Nombre (cargado)", value=st.session_state.get("__auto_loaded_nombre",""))
        responsable = st.text_input("Responsable (cargado)", value=st.session_state.get("__auto_loaded_responsable",""))
        avance = st.text_input("Avance (cargado)", value=st.session_state.get("__auto_loaded_avance",""))
        observaciones = st.text_area("Observaciones (cargado)", value=st.session_state.get("__auto_loaded_observaciones",""))
        fecha_inicio = st.date_input("Fecha de Inicio (cargado)", value=st.session_state.get("__auto_loaded_fecha_inicio", date.today()))
        fecha_termino = st.date_input("Fecha de Término (cargado)", value=st.session_state.get("__auto_loaded_fecha_termino", date.today()))

        # Botones: Guardar, Limpiar, Editar, Eliminar (todos juntos)
        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
        with b_col1:
            if st.button("💾 Guardar"):
                if not nombre.strip():
                    st.warning("Debe ingresar un nombre de tarea.")
                else:
                    datos = (
                        estado,
                        nombre.strip(),
                        responsable.strip(),
                        avance.strip(),
                        observaciones.strip(),
                        fecha_inicio.isoformat(),
                        fecha_termino.isoformat()
                    )
                    if st.session_state.modo_edicion and st.session_state.selected_id is not None:
                        actualizar_tarea(st.session_state.selected_id, datos)
                        st.success(f"Tarea ID {st.session_state.selected_id} actualizada.")
                    else:
                        agregar_tarea(datos)
                        st.success("Tarea agregada.")
                    # limpiar estado de carga automática
                    for k in ["__auto_loaded_estado","__auto_loaded_nombre","__auto_loaded_responsable",
                              "__auto_loaded_avance","__auto_loaded_observaciones",
                              "__auto_loaded_fecha_inicio","__auto_loaded_fecha_termino"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.session_state.selected_id = None
                    st.session_state.modo_edicion = False
                    st.experimental_rerun()

        with b_col2:
            if st.button("🧹 Limpiar"):
                for k in ["__auto_loaded_estado","__auto_loaded_nombre","__auto_loaded_responsable",
                          "__auto_loaded_avance","__auto_loaded_observaciones",
                          "__auto_loaded_fecha_inicio","__auto_loaded_fecha_termino"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.session_state.selected_id = None
                st.session_state.modo_edicion = False
                st.experimental_rerun()

        with b_col3:
            if st.button("✏️ Editar"):
                if st.session_state.selected_id is None:
                    st.warning("Seleccione una fila marcando la casilla en la tabla.")
                else:
                    # Forzamos recarga para que el bloque que asigna __auto_loaded_* corra
                    st.session_state.modo_edicion = False
                    st.experimental_rerun()

        with b_col4:
            if st.button("🗑️ Eliminar"):
                if st.session_state.selected_id is None:
                    st.warning("Seleccione una fila marcando la casilla en la tabla.")
                else:
                    eliminar_tarea(st.session_state.selected_id)
                    st.success(f"Tarea ID {st.session_state.selected_id} eliminada.")
                    st.session_state.selected_id = None
                    st.session_state.modo_edicion = False
                    st.experimental_rerun()

    # ---------- Tabla (derecha) ----------
    with col_right:
        st.subheader("Lista de Tareas (clic en la casilla para seleccionar)")

        # Preparamos la tabla con columna de selección (checkbox)
        df_display = df.copy()
        if df_display.empty:
            st.info("No hay tareas registradas.")
        else:
            # Insertar la columna 'Seleccionar' como False por defecto (al inicio)
            df_display.insert(0, "Seleccionar", False)

            # Renderizamos la tabla editable solo en la columna 'Seleccionar' (otras deshabilitadas)
            # Usamos data_editor para permitir checkboxes
            edited = st.data_editor(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Seleccionar": st.column_config.CheckboxColumn("Seleccionar", required=False),
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "estado": st.column_config.TextColumn("Estado", disabled=True),
                    "nombre": st.column_config.TextColumn("Nombre", disabled=True),
                    "responsable": st.column_config.TextColumn("Responsable", disabled=True),
                    "avance": st.column_config.TextColumn("Avance", disabled=True),
                    "observaciones": st.column_config.TextColumn("Observaciones", disabled=True),
                    "fecha_inicio": st.column_config.DateColumn("Inicio", disabled=True),
                    "fecha_termino": st.column_config.DateColumn("Término", disabled=True),
                },
                num_rows="dynamic"
            )

            # 'edited' es un DataFrame que refleja la tabla con los valores de 'Seleccionar'
            # Buscar filas con Seleccionar == True
            seleccionadas = edited[edited["Seleccionar"] == True]

            if not seleccionadas.empty:
                # Si hay más de una seleccionada, tomamos la primera (puedes cambiar comportamiento)
                primera = seleccionadas.iloc[0]
                st.session_state.selected_id = int(primera["id"])
                st.info(f"Fila seleccionada -> ID: {st.session_state.selected_id}")
            else:
                # Si ninguna seleccionada, limpiar selección en session_state
                st.session_state.selected_id = None

if __name__ == "__main__":
    main()




















