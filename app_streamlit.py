import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
import numpy as np

DB_FILE = "tareas.db"
EXCEL_FILE = "tareas_exportadas.xlsx"

def migrar_esquema():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("PRAGMA table_info(tareas)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'nombre' in columnas:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tareas_nueva (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tarea TEXT NOT NULL,
                    acciones TEXT,
                    fecha_inicio TEXT,
                    plazo TEXT,
                    observaciones TEXT,
                    estado TEXT DEFAULT 'Pendiente',
                    delegada TEXT
                )
            ''')
            
            conn.execute('''
                INSERT INTO tareas_nueva (id, tarea, acciones, estado, delegada)
                SELECT id, nombre, descripcion, estado, responsable
                FROM tareas
            ''')
            
            conn.execute("DROP TABLE tareas")
            conn.execute("ALTER TABLE tareas_nueva RENAME TO tareas")
            conn.commit()
            st.success("Esquema de base de datos actualizado exitosamente")

def init_db():
    migrar_esquema()
    
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarea TEXT NOT NULL,
                acciones TEXT,
                fecha_inicio TEXT,
                plazo TEXT,
                observaciones TEXT,
                estado TEXT DEFAULT 'Pendiente',
                delegada TEXT
            )
        ''')
        conn.commit()

def obtener_tareas():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM tareas", conn)
    return df

def obtener_tarea_por_id(id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
        tarea = cursor.fetchone()
        if tarea:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, tarea))
        return None

def agregar_tarea(tarea, acciones, fecha_inicio, plazo, observaciones, delegada, estado, exportar=True):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            INSERT INTO tareas (tarea, acciones, fecha_inicio, plazo, observaciones, delegada, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tarea, acciones, fecha_inicio, plazo, observaciones, delegada, estado))
        conn.commit()
    
    if exportar:
        exportar_a_excel()

def editar_tarea(id, tarea, acciones, fecha_inicio, plazo, observaciones, delegada, estado, exportar=True):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            UPDATE tareas
            SET tarea = ?, acciones = ?, fecha_inicio = ?, plazo = ?, observaciones = ?, delegada = ?, estado = ?
            WHERE id = ?
        ''', (tarea, acciones, fecha_inicio, plazo, observaciones, delegada, estado, id))
        conn.commit()
    
    if exportar:
        exportar_a_excel()

def eliminar_tarea(id, exportar=True):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('DELETE FROM tareas WHERE id = ?', (id,))
        conn.commit()
    
    if exportar:
        exportar_a_excel()

def exportar_a_excel():
    """Exporta todas las tareas a un archivo Excel"""
    tareas_df = obtener_tareas()
    if not tareas_df.empty:
        # Crear un DataFrame con las columnas necesarias
        export_df = tareas_df[['id', 'tarea', 'acciones', 'fecha_inicio', 'plazo', 
                              'observaciones', 'estado', 'delegada']].copy()
        
        # Renombrar columnas para mejor presentación
        export_df.columns = ['ID', 'Tarea', 'Acciones a Realizar', 'Fecha Inicio', 
                            'Plazo', 'Observaciones', 'Estado', 'Delegada']
        
        # Guardar en Excel
        export_df.to_excel(EXCEL_FILE, index=False)
        return True
    return False

def importar_desde_excel():
    """Importa tareas desde el archivo Excel a la base de datos"""
    try:
        # Verificar si el archivo existe
        if not os.path.exists(EXCEL_FILE):
            st.error(f"Archivo {EXCEL_FILE} no encontrado")
            return False
        
        # Leer el archivo Excel
        excel_df = pd.read_excel(EXCEL_FILE)
        
        # Verificar si está vacío
        if excel_df.empty:
            st.warning("El archivo Excel está vacío")
            return False
        
        # Renombrar columnas para coincidir con la base de datos
        column_mapping = {
            'ID': 'id',
            'Tarea': 'tarea',
            'Acciones a Realizar': 'acciones',
            'Fecha Inicio': 'fecha_inicio',
            'Plazo': 'plazo',
            'Observaciones': 'observaciones',
            'Estado': 'estado',
            'Delegada': 'delegada'
        }
        excel_df.rename(columns=column_mapping, inplace=True)
        
        # Obtener tareas existentes en la base de datos
        db_tareas = obtener_tareas()
        db_ids = set(db_tareas['id']) if not db_tareas.empty else set()
        
        # Contadores para estadísticas
        nuevas = 0
        actualizadas = 0
        
        # Procesar cada fila del Excel
        for _, row in excel_df.iterrows():
            # Convertir tipos de datos
            row = row.where(pd.notnull(row), None)
            
            # Manejar fechas
            fecha_inicio = row['fecha_inicio']
            if isinstance(fecha_inicio, pd.Timestamp):
                fecha_inicio = fecha_inicio.strftime('%Y-%m-%d')
            
            plazo = row['plazo']
            if isinstance(plazo, pd.Timestamp):
                plazo = plazo.strftime('%Y-%m-%d')
            
            # Verificar si la tarea ya existe en la base de datos
            tarea_id = row['id']
            if tarea_id in db_ids:
                # Actualizar tarea existente
                editar_tarea(
                    tarea_id,
                    row['tarea'],
                    row['acciones'],
                    fecha_inicio,
                    plazo,
                    row['observaciones'],
                    row['delegada'],
                    row['estado'],
                    exportar=False  # Evitar exportar durante la importación
                )
                actualizadas += 1
            else:
                # Insertar como nueva tarea
                agregar_tarea(
                    row['tarea'],
                    row['acciones'],
                    fecha_inicio,
                    plazo,
                    row['observaciones'],
                    row['delegada'],
                    row['estado'],
                    exportar=False  # Evitar exportar durante la importación
                )
                nuevas += 1
        
        # Exportar después de todas las operaciones para actualizar el Excel
        exportar_a_excel()
        
        return nuevas, actualizadas
    except Exception as e:
        st.error(f"Error al importar: {str(e)}")
        return None

def main():
    st.set_page_config(layout="wide", page_title="Compromisos OCT")
    init_db()
    
    # Exportar inicialmente si no existe el archivo
    if not os.path.exists(EXCEL_FILE):
        exportar_a_excel()
    
    # Estado de la sesión
    if "tarea_seleccionada" not in st.session_state:
        st.session_state["tarea_seleccionada"] = None
    if "ver_detalle" not in st.session_state:
        st.session_state["ver_detalle"] = None
    if "selected_row" not in st.session_state:
        st.session_state["selected_row"] = None
    if "current_tab" not in st.session_state:
        st.session_state["current_tab"] = "Listado de Tareas"
    if "selected_tasks" not in st.session_state:
        st.session_state["selected_tasks"] = []
    if "reset_counter" not in st.session_state:
        st.session_state["reset_counter"] = 0  # Para resetear formulario

    # Título principal
    st.markdown("<h1 style='text-align: center;'>Compromisos OCT</h1>", unsafe_allow_html=True)
    
    # Obtener tareas
    tareas_df = obtener_tareas()
    
    # Pestañas principales
    tab_list, tab_add = st.tabs(["Listado de Tareas", "Agregar Tarea"])
    
    # Controlador para cambiar pestañas
    if st.session_state["current_tab"] == "Agregar Tarea":
        tab_add.write("")
    else:
        tab_list.write("")
    
    # Contenido de la pestaña de listado
    with tab_list:
        if not tareas_df.empty:
            # Preprocesar datos para visualización
            tareas_df['terminado'] = tareas_df['estado'].apply(lambda x: 1 if x == 'Terminada' else 0)
            
            # Agregar columna de selección
            tareas_df['Seleccionar'] = False
            if st.session_state["selected_tasks"]:
                # Mantener selecciones previas
                tareas_df['Seleccionar'] = tareas_df['id'].isin(st.session_state["selected_tasks"])
            
            tareas_display = tareas_df[['Seleccionar', 'id', 'estado', 'tarea', 'acciones', 'terminado', 
                                       'delegada', 'fecha_inicio', 'plazo']]
            
            # Mostrar tabla con selección
            edited_df = st.data_editor(
                tareas_display,
                column_config={
                    "Seleccionar": st.column_config.CheckboxColumn("Seleccionar"),
                    "id": None,
                    "estado": st.column_config.TextColumn("Estado"),
                    "tarea": st.column_config.TextColumn("Tarea", width="large"),
                    "acciones": st.column_config.TextColumn("Acciones a Realizar", width="large"),
                    "terminado": st.column_config.CheckboxColumn("Terminado", disabled=True),
                    "delegada": st.column_config.TextColumn("Delegada"),
                    "fecha_inicio": st.column_config.DateColumn("F. Inicio", format="DD-MM-YYYY"),
                    "plazo": st.column_config.DateColumn("Plazo", format="DD-MM-YYYY")
                },
                hide_index=True,
                use_container_width=True,
                disabled=["id", "estado", "tarea", "acciones", "delegada", "fecha_inicio", "plazo"],
                key="editor"
            )
            
            # Actualizar selecciones
            if "editor" in st.session_state:
                selected_rows = edited_df[edited_df['Seleccionar'] == True]
                st.session_state["selected_tasks"] = selected_rows['id'].tolist()
            
            # Botones de acción
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🗑️ Eliminar"):
                    if st.session_state["selected_tasks"]:
                        for tarea_id in st.session_state["selected_tasks"]:
                            eliminar_tarea(tarea_id)
                        # Limpiamos selección y detalle
                        st.session_state["selected_tasks"] = []
                        st.session_state["ver_detalle"] = None
                        st.rerun()
                    else:
                        st.warning("Selecciona al menos una tarea")
            with col2:
                if st.button("✏️ Editar"):
                    if len(st.session_state["selected_tasks"]) == 1:
                        tarea_id = st.session_state["selected_tasks"][0]
                        st.session_state["tarea_seleccionada"] = tarea_id
                        st.session_state["current_tab"] = "Agregar Tarea"
                        st.rerun()
                    elif st.session_state["selected_tasks"]:
                        st.warning("Solo puedes editar una tarea a la vez")
                    else:
                        st.warning("Selecciona una tarea primero")
            with col3:
                if st.button("👁️ Ver Detalle"):
                    if len(st.session_state["selected_tasks"]) == 1:
                        tarea_id = st.session_state["selected_tasks"][0]
                        st.session_state["ver_detalle"] = tarea_id
                    elif st.session_state["selected_tasks"]:
                        st.warning("Solo puedes ver el detalle de una tarea a la vez")
                    else:
                        st.warning("Selecciona una tarea primero")
            
            # Mostrar detalle si está seleccionado
            if st.session_state["ver_detalle"]:
                tarea_id = st.session_state["ver_detalle"]
                # Obtenemos la tarea de la base de datos actualizada
                tarea = obtener_tarea_por_id(tarea_id)
                if tarea is None:
                    st.error("La tarea seleccionada ya no existe")
                    st.session_state["ver_detalle"] = None
                    st.rerun()
                else:
                    with st.expander(f"Detalle de la Tarea: {tarea['tarea']}", expanded=True):
                        st.markdown(f"**Tarea:**\n{tarea['tarea']}")
                        st.divider()
                        
                        st.markdown("**Acciones a Realizar:**")
                        st.markdown(f"{tarea['acciones']}")
                        st.divider()
                        
                        st.markdown("**Observaciones:**")
                        st.markdown(f"{tarea['observaciones'] or 'Sin observaciones'}")
                        
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if st.button("Cerrar Detalle"):
                                st.session_state["ver_detalle"] = None
                                st.rerun()
        else:
            st.info("No hay tareas registradas")
    
    # Contenido de la pestaña de agregar/editar
    with tab_add:
        # Si estamos en modo edición, cargamos la tarea desde la base de datos (actualizada)
        if st.session_state["tarea_seleccionada"]:
            tarea_id = st.session_state["tarea_seleccionada"]
            tarea = obtener_tarea_por_id(tarea_id)
            if tarea is None:
                st.error("La tarea seleccionada ya no existe")
                st.session_state["tarea_seleccionada"] = None
                st.session_state["current_tab"] = "Listado de Tareas"
                st.rerun()
            modo = "edición"
        else:
            tarea = {
                "tarea": "",
                "acciones": "",
                "fecha_inicio": datetime.now().strftime("%Y-%m-%d"),
                "plazo": datetime.now().strftime("%Y-%m-%d"),
                "observaciones": "",
                "delegada": "",
                "estado": "Pendiente"
            }
            modo = "agregar"
        
        st.subheader(f"{'Editar' if modo == 'edición' else 'Agregar'} Tarea")
        
        # Generar claves únicas para cada widget usando el contador de reset
        key_suffix = f"{modo}_{st.session_state.reset_counter}"
        tarea_key = f"tarea_nombre_{key_suffix}"
        acciones_key = f"acciones_{key_suffix}"
        fecha_inicio_key = f"fecha_inicio_{key_suffix}"
        plazo_key = f"plazo_{key_suffix}"
        observaciones_key = f"observaciones_{key_suffix}"
        delegada_key = f"delegada_{key_suffix}"
        estado_key = f"estado_{key_suffix}"
        
        # Formulario
        tarea_nombre = st.text_input("Tarea", value=tarea["tarea"], key=tarea_key)
        acciones = st.text_area("Acciones a Realizar", value=tarea["acciones"], height=150, key=acciones_key)
        
        col1, col2 = st.columns(2)
        with col1:
            # Convertimos la fecha string a objeto date
            fecha_inicio_val = datetime.strptime(tarea["fecha_inicio"], "%Y-%m-%d").date() if tarea["fecha_inicio"] else datetime.now().date()
            fecha_inicio = st.date_input("F. Inicio", value=fecha_inicio_val, key=fecha_inicio_key)
        with col2:
            plazo_val = datetime.strptime(tarea["plazo"], "%Y-%m-%d").date() if tarea["plazo"] else datetime.now().date()
            plazo = st.date_input("Plazo", value=plazo_val, key=plazo_key)
        
        observaciones = st.text_area("Observaciones", value=tarea["observaciones"], height=100, key=observaciones_key)
        delegada = st.text_input("Delegada", value=tarea["delegada"], key=delegada_key)
        estado = st.selectbox("Estado", 
                              ["Pendiente", "En Proceso", "Terminada"], 
                              index=["Pendiente", "En Proceso", "Terminada"].index(tarea["estado"]) if tarea["estado"] in ["Pendiente", "En Proceso", "Terminada"] else 0, 
                              key=estado_key)
        
        # Botones de acción - Ahora en 4 columnas
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        with col_btn1:
            if st.button("💾 Guardar"):
                if tarea_nombre:
                    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
                    plazo_str = plazo.strftime("%Y-%m-%d")
                    
                    if modo == "agregar":
                        agregar_tarea(tarea_nombre, acciones, fecha_inicio_str, 
                                     plazo_str, observaciones, delegada, estado)
                        st.success("Tarea agregada exitosamente")
                    else:
                        editar_tarea(tarea_id, tarea_nombre, acciones, fecha_inicio_str,
                                    plazo_str, observaciones, delegada, estado)
                        st.success("Tarea actualizada exitosamente")
                    
                    st.session_state["tarea_seleccionada"] = None
                    st.session_state["current_tab"] = "Listado de Tareas"
                    st.rerun()
                else:
                    st.warning("El nombre de la tarea es obligatorio")
        
        with col_btn2:
            if st.button("❌ Cancelar"):
                st.session_state["tarea_seleccionada"] = None
                st.session_state["current_tab"] = "Listado de Tareas"
                st.rerun()
        
        with col_btn3:
            if st.button("🧹 Limpiar"):
                # Incrementar contador para generar nuevas claves
                st.session_state.reset_counter += 1
                st.rerun()
        
        with col_btn4:
            if st.button("📥 Importar desde Excel", help="Importar tareas desde el archivo Excel"):
                resultado = importar_desde_excel()
                if resultado:
                    nuevas, actualizadas = resultado
                    st.success(f"Importación exitosa: {nuevas} nuevas tareas, {actualizadas} actualizadas")
                    st.rerun()
                else:
                    st.error("Error en la importación")
        
        # Información sobre el archivo Excel
        st.info(f"Todas las tareas se sincronizan automáticamente con el archivo: {EXCEL_FILE}")
        st.info("Usa el botón 'Importar desde Excel' para cargar datos desde este archivo")

if __name__ == "__main__":
    main()




















