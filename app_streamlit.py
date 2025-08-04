import streamlit as st
import pandas as pd
import sqlite3
from modelo_tarea import Tarea

DB_NAME = "tareas.db"

def conectar():
    return sqlite3.connect(DB_NAME)

def obtener_todas():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM tareas", conn)
    conn.close()
    return df

# Streamlit Layout
st.set_page_config(page_title="Compromisos OCT", layout="wide")
st.title("📋 Compromisos OCT - ISL")

# Cargar Tareas
df_tareas = obtener_todas()

# Mostrar tabla de tareas
st.dataframe(df_tareas)

# Exportar a Excel
st.download_button(
    "📥 Descargar Excel",
    data=df_tareas.to_csv(index=False).encode('utf-8'),
    file_name="tareas_exportadas.csv",
    mime="text/csv"
)

