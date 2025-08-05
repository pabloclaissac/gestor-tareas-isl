import streamlit as st
import pandas as pd
import io

# Simulando una base de datos temporal
if 'df_tareas' not in st.session_state:
    st.session_state.df_tareas = pd.DataFrame({
        'ID': [1, 2, 3, 4],
        'Estado': ['Terminada', 'Terminada', 'Pendiente', 'Pendiente'],
        'Tarea': ['OneDrive', 'Informe PAC', 'Revisar presupuesto', 'Enviar reporte'],
        'Acciones': ['Actualizar OneDrive', 'Solicitar PAC', 'Analizar costos', 'Redactar informe'],
        'Terminado': [True, True, False, False],
        'Delegada': [False, False, True, False],
        'F_Inicio': ['2025-02-10', '2025-02-11', '2025-02-12', '2025-02-13'],
        'Plazo': ['2025-02-15', '2025-02-16', '2025-02-20', '2025-02-25']
    })

df = st.session_state.df_tareas

# === Estilo CSS ===
st.markdown("""
    <style>
    .centered {text-align: center;}
    .button-bar button {
        margin-right: 10px;
        background-color: #0F69B4;
        color: white;
        border-radius: 5px;
    }
    .scrollable-table {
        overflow-y: auto;
        height: 500px;
    }
    th, td {
        text-align: center !important;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# === ENCABEZADO ===
st.markdown("<h2 class='centered'>Compromisos OCT</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.metric("Tareas Completadas", df['Terminado'].sum())
with col2:
    st.metric("Tareas Pendientes", (df['Terminado'] == False).sum())

# === FORMULARIO ===
st.subheader("Ingreso / Edición de Tareas")
with st.form("form_tarea"):
    col1, col2 = st.columns(2)
    with col1:
        tarea = st.text_input("Tarea")
        acciones = st.text_input("Acciones a Realizar")
        terminado = st.checkbox("Terminado")
    with col2:
        delegada = st.checkbox("Delegada")
        fecha_inicio = st.date_input("F. Inicio")
        plazo = st.date_input("Plazo")

    submitted = st.form_submit_button("Guardar")
    if submitted:
        new_id = df['ID'].max() + 1 if not df.empty else 1
        nuevo = {
            'ID': new_id,
            'Estado': 'Terminada' if terminado else 'Pendiente',
            'Tarea': tarea,
            'Acciones': acciones,
            'Terminado': terminado,
            'Delegada': delegada,
            'F_Inicio': fecha_inicio,
            'Plazo': plazo
        }
        st.session_state.df_tareas = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
        st.experimental_rerun()

# === LISTADO DE TAREAS ===
st.subheader("Listado de Tareas")
st.markdown("<div class='scrollable-table'>", unsafe_allow_html=True)
st.dataframe(st.session_state.df_tareas, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

# === BARRA DE BOTONES ===
st.markdown("""
<div class='button-bar'>
    <button>Agregar tarea</button>
    <button>Eliminar</button>
    <button>Editar</button>
    <button>Ver detalle</button>
    <button>Exportar a Excel</button>
    <button>Importar desde Excel</button>
</div>
""", unsafe_allow_html=True)

# === EXPORTAR A EXCEL ===
excel_buffer = io.BytesIO()
st.session_state.df_tareas.to_excel(excel_buffer, index=False)
st.download_button("Descargar Excel", data=excel_buffer.getvalue(), file_name="tareas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")








