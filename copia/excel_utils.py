# excel_utils.py
import sqlite3
import pandas as pd

DB_NAME = "tareas.db"
EXCEL_FILE = "tareas_exportadas.xlsx"

def exportar_a_excel():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM tareas", conn)
    conn.close()
    df.to_excel(EXCEL_FILE, index=False)


