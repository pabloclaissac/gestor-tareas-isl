import streamlit as st
import pandas as pd
import io

# Simulación de base de datos
tasks_data = [
    {"ID": 1, "Task": "Actualizar informe mensual", "Status": "Completada"},
    {"ID": 2, "Task": "Revisar presupuestos", "Status": "Pendiente"},
    {"ID": 3, "Task": "Enviar reporte de avances", "Status": "Pendiente"}
]
df_tasks = pd.DataFrame(tasks_data)

# Configuración de página
st.set_page_config(layout="wide")

# Estilo CSS personalizado
st.markdown("""
    <style>
    .fixed-header {
        position: fixed;
        top: 0; left: 0; right: 0;
        background-color: white;
        z-index: 1000;
        padding: 10px 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .spacer { margin-top: 80px; }
    .task-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

# === ENCABEZADO FIJO ===
completed = (df_tasks['Status'] == 'Completada').sum()
pending = (df_tasks['Status'] == 'Pendiente').sum()

st.markdown(f"""
<div class='fixed-header'>
    <h2 style='display:inline-block; margin-right:50px;'>Tareas Completadas: {completed}</h2>
    <h2 style='display:inline-block;'>Tareas Pendientes: {pending}</h2>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)

# === ÁREAS LATERALES ===
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Ingreso / Edición de Tareas")
    with st.form("form_tarea"):
        tarea = st.text_input("Tarea")
        estado = st.selectbox("Estado", ["Pendiente", "Completada"])
        submitted = st.form_submit_button("Guardar")
        if submitted:
            st.success(f"Tarea '{tarea}' guardada como {estado}.")

with col2:
    st.header("Listado de Tareas")
    task_container = st.container()
    for _, row in df_tasks.iterrows():
        with task_container:
            st.markdown(f"""
                <div class='task-card'>
                    <strong>{row['Task']}</strong><br>
                    Estado: {row['Status']}<br><br>
                    <button style='margin-right:10px;'>Editar</button>
                    <button>Eliminar</button>
                </div>
            """, unsafe_allow_html=True)

# Exportar a Excel
buffer = io.BytesIO()
df_tasks.to_excel(buffer, index=False)
st.download_button("📥 Exportar a Excel", data=buffer.getvalue(), file_name="tareas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")







