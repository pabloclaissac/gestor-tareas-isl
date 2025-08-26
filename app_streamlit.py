import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
import numpy as np
import base64  # Añadido para manejar la imagen

DB_FILE = "tareas.db"
EXCEL_FILE = "tareas_exportadas.xlsx"
EXCEL_EXPORTADO = "Excel_Exportado.xlsx"  # Nuevo nombre para exportación manual

# =========================
# CONVERTIR IMAGEN LOCAL A BASE64
# =========================
def image_to_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.error(f"Archivo de imagen no encontrado: {path}")
        return None

# Cargar imagen
IMAGEN_LOCAL = "LOGO-PROPIO-ISL-2023-CMYK-01.png"
img_base64 = image_to_base64(IMAGEN_LOCAL)
img_src = f"data:image/png;base64,{img_base64}" if img_base64 else None

# =========================
# Configuración del encabezado
# =========================
COLOR_FONDO = "#0F69B4"  # Azul
TITULO = "COMPROMISOS OCT"
SUBTITULO = "Coordinación Territorial"

def init_db():
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
                delegada TEXT,
                fecha_termino TEXT
            )
        ''')
        conn.commit()

    migrar_esquema()

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
                    delegada TEXT,
                    fecha_termino TEXT
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

        # Asegurarse de que la columna fecha_termino exista
        cursor = conn.execute("PRAGMA table_info(tareas)")
        columnas = [col[1] for col in cursor.fetchall()]
        if 'fecha_termino' not in columnas:
            conn.execute("ALTER TABLE tareas ADD COLUMN fecha_termino TEXT")
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
    fecha_termino = datetime.now().strftime("%Y-%m-%d") if estado == 'Terminada' else None
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            INSERT INTO tareas (tarea, acciones, fecha_inicio, plazo, observaciones, delegada, estado, fecha_termino)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (tarea, acciones, fecha_inicio, plazo, observaciones, delegada, estado, fecha_termino))
        conn.commit()
    
    if exportar:
        exportar_a_excel()

def editar_tarea(id, tarea, acciones, fecha_inicio, plazo, observaciones, delegada, estado, exportar=True):
    tarea_actual = obtener_tarea_por_id(id)
    estado_actual = tarea_actual['estado'] if tarea_actual else None
    
    if estado == 'Terminada' and estado_actual != 'Terminada':
        fecha_termino = datetime.now().strftime("%Y-%m-%d")
    elif estado != 'Terminada' and estado_actual == 'Terminada':
        fecha_termino = None
    else:
        fecha_termino = tarea_actual.get('fecha_termino') if tarea_actual else None
    
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            UPDATE tareas
            SET tarea = ?, acciones = ?, fecha_inicio = ?, plazo = ?, 
                observaciones = ?, delegada = ?, estado = ?, fecha_termino = ?
            WHERE id = ?
        ''', (tarea, acciones, fecha_inicio, plazo, observaciones, delegada, estado, fecha_termino, id))
        conn.commit()
    
    if exportar:
        exportar_a_excel()

def actualizar_estado(id, nuevo_estado):
    tarea = obtener_tarea_por_id(id)
    if not tarea:
        return
    
    if nuevo_estado == 'Terminada' and tarea['estado'] != 'Terminada':
        fecha_termino = datetime.now().strftime("%Y-%m-%d")
    elif nuevo_estado != 'Terminada' and tarea['estado'] == 'Terminada':
        fecha_termino = None
    else:
        fecha_termino = tarea.get('fecha_termino')
    
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            UPDATE tareas
            SET estado = ?, fecha_termino = ?
            WHERE id = ?
        ''', (nuevo_estado, fecha_termino, id))
        conn.commit()
    exportar_a_excel()

def eliminar_tarea(id, exportar=True):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('DELETE FROM tareas WHERE id = ?', (id,))
        conn.commit()
    
    if exportar:
        exportar_a_excel()

def exportar_a_excel(nombre_archivo=EXCEL_FILE):
    """Exporta todas las tareas a un archivo Excel"""
    tareas_df = obtener_tareas()
    if not tareas_df.empty:
        export_df = tareas_df[['id', 'tarea', 'acciones', 'fecha_inicio', 'plazo', 
                              'observaciones', 'estado', 'delegada', 'fecha_termino']].copy()
        
        export_df.columns = ['ID', 'Tarea', 'Acciones a Realizar', 'Fecha Inicio', 
                            'Plazo', 'Observaciones', 'Estado', 'Delegada a', 'F.Término']
        
        export_df.to_excel(nombre_archivo, index=False)
        return True
    return False

def importar_desde_excel():
    try:
        if not os.path.exists(EXCEL_FILE):
            st.error(f"Archivo {EXCEL_FILE} no encontrado")
            return False
        
        excel_df = pd.read_excel(EXCEL_FILE)
        
        if excel_df.empty:
            st.warning("El archivo Excel está vacío")
            return False
        
        columnas_esperadas = ['ID', 'Tarea', 'Acciones a Realizar', 'Fecha Inicio', 
                             'Plazo', 'Observaciones', 'Estado', 'Delegada a', 'F.Término']
        
        for col in excel_df.columns:
            if col not in columnas_esperadas:
                excel_df = excel_df.drop(columns=[col])
        
        column_mapping = {
            'ID': 'id',
            'Tarea': 'tarea',
            'Acciones a Realizar': 'acciones',
            'Fecha Inicio': 'fecha_inicio',
            'Plazo': 'plazo',
            'Observaciones': 'observaciones',
            'Estado': 'estado',
            'Delegada a': 'delegada',
            'F.Término': 'fecha_termino'
        }
        excel_df.rename(columns=column_mapping, inplace=True)
        
        db_tareas = obtener_tareas()
        db_ids = set(db_tareas['id']) if not db_tareas.empty else set()
        
        nuevas = 0
        actualizadas = 0
        
        for _, row in excel_df.iterrows():
            row = row.where(pd.notnull(row), None)
            
            fecha_inicio = row['fecha_inicio']
            if isinstance(fecha_inicio, pd.Timestamp):
                fecha_inicio = fecha_inicio.strftime('%Y-%m-%d')
            
            plazo = row['plazo']
            if isinstance(plazo, pd.Timestamp):
                plazo = plazo.strftime('%Y-%m-%d')
            
            fecha_termino = row['fecha_termino']
            if isinstance(fecha_termino, pd.Timestamp):
                fecha_termino = fecha_termino.strftime('%Y-%m-%d')
            
            tarea_id = row['id']
            if tarea_id in db_ids:
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute('''
                        UPDATE tareas
                        SET tarea = ?, acciones = ?, fecha_inicio = ?, plazo = ?, 
                            observaciones = ?, delegada = ?, estado = ?, fecha_termino = ?
                        WHERE id = ?
                    ''', (
                        row['tarea'],
                        row['acciones'],
                        fecha_inicio,
                        plazo,
                        row['observaciones'],
                        row['delegada'],
                        row['estado'],
                        fecha_termino,
                        tarea_id
                    ))
                    conn.commit()
                actualizadas += 1
            else:
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute('''
                        INSERT INTO tareas (tarea, acciones, fecha_inicio, plazo, 
                                          observaciones, delegada, estado, fecha_termino)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['tarea'],
                        row['acciones'],
                        fecha_inicio,
                        plazo,
                        row['observaciones'],
                        row['delegada'],
                        row['estado'],
                        fecha_termino
                    ))
                    conn.commit()
                nuevas += 1
        
        exportar_a_excel()
        
        return nuevas, actualizadas
    except Exception as e:
        st.error(f"Error al importar: {str(e)}")
        return None

def main():
    st.set_page_config(layout="wide", page_title="Compromisos OCT")
    init_db()
    
    # Estilos CSS
    st.markdown(f"""
    <style>
        .header-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: {COLOR_FONDO};
            height: 85px;
            width: 100%;
            color: white;
            position: relative;
            margin: -1rem -1rem 1.2rem -1rem;
        }}
        .header-logo {{
            position: absolute;
            left: 20px;
            top: 5px;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }}
        .header-logo img {{
            height: 60px;
        }}
        .header-subtitle {{
            position: absolute;
            bottom: 5px;
            left: 20px;
            font-size: 10px;
        }}
        .header-title {{
            font-size: 20px;
            font-weight: bold;
        }}
        .main-container {{
            display: flex;
            flex-direction: column;
            height: calc(100vh - 150px) !important;
            min-height: 500px !important;
        }}
        .table-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: 300px;
        }}
        .stDataFrame, .stDataEditor {{
            flex: 1;
            min-height: 200px;
        }}
        .button-container {{
            margin-top: auto;
            padding-bottom: 5px !important;
        }}
        div[data-testid="stVerticalBlock"] {{
            height: 100% !important;
        }}
        div[data-testid="stHorizontalBlock"] {{
            height: 100% !important;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Encabezado
    if img_src:
        st.markdown(f"""
        <div class="header-container">
            <div class="header-logo">
                <img src="{img_src}" alt="Logo">
            </div>
            <div class="header-subtitle">{SUBTITULO}</div>
            <div class="header-title">{TITULO}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; 
                    background-color: {COLOR_FONDO}; height: 85px; width: 100%; 
                    color: white; position: relative; margin: -1rem -1rem 1.2rem -1rem;">
            <div style="position: absolute; left: 20px; top: 5px; display: flex; 
                       flex-direction: column; align-items: flex-start;">
                <div style="font-size: 24px; font-weight: bold;">ISL</div>
            </div>
            <div style="position: absolute; bottom: 5px; left: 20px; font-size: 10px;">
                {SUBTITULO}
            </div>
            <div style="font-size: 20px; font-weight: bold;">{TITULO}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if not os.path.exists(EXCEL_FILE):
        exportar_a_excel()
    
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
        st.session_state["reset_counter"] = 0
    if "last_interaction" not in st.session_state:
        st.session_state["last_interaction"] = {"type": None, "id": None}

    tareas_df = obtener_tareas()
    
    tabs = ["Listado de Tareas", "Agregar Tarea"]
    current_tab = st.selectbox(
        "Seleccione una vista:",
        tabs,
        index=tabs.index(st.session_state["current_tab"])
    )
    
    if current_tab == "Listado de Tareas":
        st.session_state["current_tab"] = "Listado de Tareas"
        
        with st.container():
            if not tareas_df.empty:
                tareas_df['terminado'] = tareas_df['estado'].apply(lambda x: 1 if x == 'Terminada' else 0)
                tareas_df['delegada_bool'] = tareas_df['delegada'].apply(lambda x: 1 if x and str(x).strip() != '' else 0)
                tareas_df['Seleccionar'] = False
                if st.session_state["selected_tasks"]:
                    tareas_df['Seleccionar'] = tareas_df['id'].isin(st.session_state["selected_tasks"])
                tareas_df['fecha_termino'] = pd.to_datetime(tareas_df['fecha_termino'], errors='coerce')
                
                tareas_display = tareas_df[['Seleccionar', 'id', 'estado', 'tarea', 'acciones', 'terminado', 
                                           'delegada_bool', 'delegada', 'fecha_inicio', 'plazo', 'fecha_termino']]
                
                with st.container():
                    edited_df = st.data_editor(
                        tareas_display,
                        column_config={
                            "Seleccionar": st.column_config.CheckboxColumn("Seleccionar"),
                            "id": None,
                            "estado": st.column_config.TextColumn("Estado"),
                            "tarea": st.column_config.TextColumn("Tarea", width="large"),
                            "acciones": st.column_config.TextColumn("Acciones a Realizar", width="large"),
                            "terminado": st.column_config.CheckboxColumn("Terminado"),
                            "delegada_bool": st.column_config.CheckboxColumn("Delegada"),
                            "delegada": st.column_config.TextColumn("Delegada a"),
                            "fecha_inicio": st.column_config.DateColumn("F. Inicio", format="DD-MM-YYYY"),
                            "plazo": st.column_config.DateColumn("Plazo", format="DD-MM-YYYY"),
                            "fecha_termino": st.column_config.DateColumn("F.Término", format="DD-MM-YYYY")
                        },
                        hide_index=True,
                        use_container_width=True,
                        disabled=["id", "estado", "tarea", "acciones", "delegada", 
                                  "fecha_inicio", "plazo", "fecha_termino"],
                        key="editor",
                        height=580
                    )

                seleccionados_actuales = edited_df[edited_df['Seleccionar'] == True]['id'].tolist()
                terminados_actuales = edited_df[edited_df['terminado'] == True]['id'].tolist()

                if len(seleccionados_actuales) > 1:
                    ultima = seleccionados_actuales[-1]
                    edited_df['Seleccionar'] = edited_df['id'] == ultima
                    st.session_state["selected_tasks"] = [ultima]
                    st.rerun()
                elif len(seleccionados_actuales) == 1:
                    st.session_state["selected_tasks"] = seleccionados_actuales

                for _, row in edited_df.iterrows():
                    tarea_original = tareas_df[tareas_df['id'] == row['id']].iloc[0]
                    if row['terminado'] != tarea_original['terminado']:
                        nuevo_estado = 'Terminada' if row['terminado'] else 'Pendiente'
                        actualizar_estado(row['id'], nuevo_estado)
                        st.rerun()

                # --- Botones ---
                with st.container():
                    st.markdown('<div class="button-container">', unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns(4)  # ahora 4 columnas
                    with col1:
                        if st.button("🗑️ Eliminar"):
                            if st.session_state["selected_tasks"]:
                                for tarea_id in st.session_state["selected_tasks"]:
                                    eliminar_tarea(tarea_id)
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
                    with col4:
                        if st.button("📤 Exportar Excel"):
                            if exportar_a_excel(EXCEL_EXPORTADO):
                                with open(EXCEL_EXPORTADO, "rb") as f:
                                    st.download_button(
                                        label="⬇️ Descargar Excel",
                                        data=f,
                                        file_name=EXCEL_EXPORTADO,
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                                st.success("Archivo listo para descargar")
                            else:
                                st.warning("No hay tareas para exportar")
                
                # --- Detalle ---
                if st.session_state["ver_detalle"]:
                    tarea_id = st.session_state["ver_detalle"]
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
                            st.divider()
                            st.markdown("**Estado:**")
                            st.markdown(f"{tarea['estado']}")
                            st.divider()
                            st.markdown("**Delegada a:**")
                            st.markdown(f"{tarea['delegada'] or 'No delegada'}")
                            st.divider()
                            st.markdown("**Fecha Inicio:**")
                            st.markdown(f"{tarea['fecha_inicio']}")
                            st.divider()
                            st.markdown("**Plazo:**")
                            st.markdown(f"{tarea['plazo'] or 'Sin plazo definido'}")
                            st.divider()
                            st.markdown("**Fecha Término:**")
                            st.markdown(f"{tarea['fecha_termino'] or 'Tarea aún no finalizada'}")
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                if st.button("Cerrar Detalle"):
                                    st.session_state["ver_detalle"] = None
                                    st.rerun()
            else:
                st.info("No hay tareas registradas")
    
    else:  # Agregar Tarea
        st.session_state["current_tab"] = "Agregar Tarea"
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
                "estado": "Pendiente",
                "fecha_termino": None
            }
            modo = "agregar"
        
        st.subheader(f"{'Editar' if modo == 'edición' else 'Agregar'} Tarea")
        
        key_suffix = f"{modo}_{st.session_state.reset_counter}"
        tarea_key = f"tarea_nombre_{key_suffix}"
        acciones_key = f"acciones_{key_suffix}"
        fecha_inicio_key = f"fecha_inicio_{key_suffix}"
        plazo_key = f"plazo_{key_suffix}"
        observaciones_key = f"observaciones_{key_suffix}"
        delegada_key = f"delegada_{key_suffix}"
        estado_key = f"estado_{key_suffix}"
        
        tarea_nombre = st.text_input("Tarea", value=tarea["tarea"], key=tarea_key)
        acciones = st.text_area("Acciones a Realizar", value=tarea["acciones"], height=150, key=acciones_key)
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio_val = datetime.strptime(tarea["fecha_inicio"], "%Y-%m-%d").date() if tarea["fecha_inicio"] else datetime.now().date()
            fecha_inicio = st.date_input("F. Inicio", value=fecha_inicio_val, key=fecha_inicio_key)
        with col2:
            plazo_val = datetime.strptime(tarea["plazo"], "%Y-%m-%d").date() if tarea["plazo"] else datetime.now().date()
            plazo = st.date_input("Plazo", value=plazo_val, key=plazo_key)
        
        observaciones = st.text_area("Observaciones", value=tarea["observaciones"], height=100, key=observaciones_key)
        delegada = st.text_input("Delegada a", value=tarea["delegada"], key=delegada_key)
        estado = st.selectbox("Estado", 
                              ["Pendiente", "En Proceso", "Terminada"], 
                              index=["Pendiente", "En Proceso", "Terminada"].index(tarea["estado"]) if tarea["estado"] in ["Pendiente", "En Proceso", "Terminada"] else 0, 
                              key=estado_key)
        
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
        
        st.info(f"Todas las tareas se sincronizan automáticamente con el archivo: {EXCEL_FILE}")
        st.info("Usa el botón 'Importar desde Excel' para cargar datos desde este archivo")

if __name__ == "__main__":
    main()
