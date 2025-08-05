# app_streamlit.py
import streamlit as st
import pandas as pd
from modelo_tarea import Tarea
import db
import io

# === Configuración de Página ===
st.set_page_config(layout="wide", page_title="Compromisos OCT")
st.markdown("""<style>.block-container {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

# === Inicializar DB ===
db.init_db()

def load_tareas():
    data = db.obtener_todas()
    columns = ["id", "estado", "nombre", "compromiso", "terminado", "delegada", "fecha_inicio", "plazo", "fecha_realizacion", "observaciones"]
    return pd.DataFrame(data, columns=columns)

df_tareas = load_tareas()

# === Layout Principal ===
col_form, col_tabla = st.columns([1, 2])

# === Sección de Formulario ===
with col_form:
    st.markdown("<h3 style='color:#0F69B4;'>Formulario de Tareas</h3>", unsafe_allow_html=True)

    if "editando" not in st.session_state:
        st.session_state.editando = False
        st.session_state.tarea_actual = None

    nombre = st.text_input("Tarea", value=st.session_state.tarea_actual['nombre'] if st.session_state.editando else "")
    compromiso = st.text_input("Acciones a Realizar", value=st.session_state.tarea_actual['compromiso'] if st.session_state.editando else "")
    fecha_inicio = st.date_input("Fecha de Inicio")
    plazo = st.date_input("Plazo")
    observaciones = st.text_area("Observaciones", value=st.session_state.tarea_actual['observaciones'] if st.session_state.editando else "")

    col1, col2 = st.columns(2)
    terminado = col1.checkbox("Terminada", value=st.session_state.tarea_actual['terminado'] if st.session_state.editando else False)
    delegada = col2.checkbox("Delegada", value=st.session_state.tarea_actual['delegada'] if st.session_state.editando else False)

    btn_col1, btn_col2 = st.columns(2)
    if btn_col1.button("Guardar"):
        tarea = Tarea(
            id=st.session_state.tarea_actual['id'] if st.session_state.editando else None,
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
        if st.session_state.editando:
            db.actualizar_tarea(tarea)
            st.success("Tarea actualizada correctamente.")
        else:
            db.agregar_tarea(tarea)
            st.success("Tarea agregada correctamente.")
        st.session_state.editando = False
        st.experimental_rerun()

    if btn_col2.button("Limpiar Formulario"):
        st.session_state.editando = False
        st.experimental_rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # Importar / Exportar
    col_exp, col_imp = st.columns(2)
    with col_exp:
        buffer = io.BytesIO()
        df_tareas.to_excel(buffer, index=False)
        st.download_button("Exportar a Excel", data=buffer.getvalue(), file_name="tareas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with col_imp:
        archivo_excel = st.file_uploader("Importar desde Excel", type="xlsx")
        if archivo_excel:
            db.importar_desde_excel(archivo_excel)
            st.success("Tareas importadas.")
            st.experimental_rerun()

# === Sección de Tabla ===
with col_tabla:
    st.markdown("<h3 style='color:#0F69B4;'>Listado de Tareas</h3>", unsafe_allow_html=True)

    for idx, row in df_tareas.iterrows():
        with st.container():
            bg_color = "#DDEFFB" if row['estado'] == "Terminada" else "#FDE9E9"
            st.markdown(f"""
                <div style='background-color:{bg_color}; padding:10px; border-radius:10px; margin-bottom:10px;'>
                    <b>{row['nombre']}</b> - {row['estado']}<br>
                    <small>{row['compromiso']}</small>
                </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1,1,2])

            if col1.button("Editar", key=f"edit_{row['id']}"):
                st.session_state.editando = True
                st.session_state.tarea_actual = row.to_dict()
                st.experimental_rerun()

            if col2.button("Eliminar", key=f"delete_{row['id']}"):
                db.eliminar_tarea(row['id'])
                st.warning(f"Tarea '{row['nombre']}' eliminada.")
                st.experimental_rerun()

            if col3.button("Ver Detalle", key=f"detail_{row['id']}"):
                st.info(f"Observaciones: {row['observaciones']}")

# === Métricas ===
completadas = df_tareas['terminado'].sum()
total = len(df_tareas)
st.sidebar.metric("Completadas", f"{int(completadas)}/{total}")
st.sidebar.metric("Pendientes", f"{int(total-completadas)}/{total}")





