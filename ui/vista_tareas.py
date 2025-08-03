import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap import Frame, Button, Label, Entry, StringVar, Style
from ttkbootstrap.widgets import Meter, DateEntry
from modelo_tarea import Tarea
from datetime import datetime
import openpyxl
import db
from db import agregar_tarea, actualizar_tarea, eliminar_tarea, obtener_todas
from excel_utils import exportar_a_excel

class VistaTareas(Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        db.init_db()
        self.tareas = []
        self.build_ui()
        self.cargar_tareas()

    def build_ui(self):
        style = Style()

        # Estilo personalizado para botones con fondo rosado y texto blanco
        style.configure('MyCustom.TButton',
                        font=('Arial', 9, 'bold'),
                        foreground='white',
                        background='#0F69B4',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        relief='flat',
                        padding=6)

        style.map('MyCustom.TButton',
                  background=[('active', '#DDEFFB'), ('disabled', '#0F69B4')],
                  foreground=[('active', '#0F69B4'), ('disabled', '#E0DADA')])

        Label(self, text="Compromisos OCT", font=("Arial", 15, "bold")).pack(pady=15)

        meter_frame = Frame(self)
        meter_frame.pack(pady=10)

        self.meter = Meter(meter_frame, amountused=0, amounttotal=100, meterthickness=15,
                        bootstyle="primary", subtext="Tareas Completadas",
                        textfont="Helvetica 12 bold", metersize=175)
        self.meter.pack(side="left", padx=20)

        self.pending_meter = Meter(meter_frame, amountused=0, amounttotal=100, meterthickness=15,
                                bootstyle="danger", subtext="Tareas Pendientes",
                                textfont="Helvetica 12 bold", metersize=175)
        self.pending_meter.pack(side="left", padx=20)

        columns = ("id", "estado", "nombre", "compromiso", "terminado", "delegada",
                "fecha_inicio", "plazo", "fecha_realizacion", "observaciones")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse", height=10)

        style.configure("Treeview", font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 9, "bold"))
        style.configure("Treeview", rowheight=35)
        style.configure("Treeview.Heading", background="#0F69B4", foreground="white")

        style.map("Treeview",
                background=[('selected', '#DDEFFB')],  # fondo azul claro para la fila seleccionada
                foreground=[('selected', '#EA7A85')])    # texto blanco al seleccionar




        self.tree.pack(fill="both", expand=True)

        headers = ["ID", "Estado", "Tarea", "Acciones a Realizar", "Terminado", "Delegada",
                "F. Inicio", "Plazo", "F. Realización", "Observaciones"]

        anchos = {
            "id": 30,
            "estado": 100,
            "nombre": 450,
            "compromiso": 450,
            "terminado": 80,
            "delegada": 80,
            "fecha_inicio": 100,
            "plazo": 100,
            "fecha_realizacion": 100,
            "observaciones": 450
        }

        anchor_cols = {
            "id": "center",
            "estado": "center",
            "nombre": "w",       # izquierda
            "compromiso": "w",   # izquierda
            "terminado": "center",
            "delegada": "center",
            "fecha_inicio": "center",
            "plazo": "center",
            "fecha_realizacion": "center",
            "observaciones": "w"  # izquierda
        }

        for col, text in zip(columns, headers):
            self.tree.heading(col, text=text)
            self.tree.column(col, anchor=anchor_cols.get(col, "center"), width=anchos.get(col, 100), stretch=False)

        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_tree_doble_click)

        btn_frame = Frame(self)
        btn_frame.pack(pady=10)

        Button(btn_frame, text="Agregar tarea", style='MyCustom.TButton', width=15, command=self.abrir_formulario).pack(side="left", padx=5)
        Button(btn_frame, text="Eliminar", style='MyCustom.TButton', width=15, command=self.eliminar_tarea).pack(side="left", padx=5)
        Button(btn_frame, text="Editar", style='MyCustom.TButton', width=15, command=self.editar_tarea).pack(side="left", padx=5)
        Button(btn_frame, text="Ver detalle", style='MyCustom.TButton', width=15, command=self.ver_detalle).pack(side="left", padx=5)
        Button(btn_frame, text="Exportar a Excel", style='MyCustom.TButton', width=15, command=exportar_a_excel).pack(side="left", padx=5)
        Button(btn_frame, text="Importar desde Excel", style='MyCustom.TButton', width=20, command=self.importar_tareas_desde_excel).pack(side="left", padx=5)
    
    def cargar_tareas(self): 
        self.tree.delete(*self.tree.get_children())
        filas = obtener_todas()
        self.tareas = [Tarea(*fila) for fila in filas]

        completadas = 0
        for tarea in self.tareas:
            terminado = "\u2611" if tarea.terminado else "\u2610"
            delegada = "\u2611" if tarea.delegada else "\u2610"
            estado = "Terminada" if tarea.terminado else "Pendiente"

            def formatear_fecha(fecha):
                if isinstance(fecha, str):
                    return fecha.split()[0] if fecha.strip() != "" else ""
                return fecha or ""

            fecha_inicio = formatear_fecha(tarea.fecha_inicio)
            plazo = formatear_fecha(tarea.plazo)
            fecha_realizacion = formatear_fecha(tarea.fecha_realizacion)

            values = (
                tarea.id,
                estado,
                tarea.nombre or "",
                tarea.compromiso or "",
                terminado,
                delegada,
                fecha_inicio,
                plazo,
                fecha_realizacion,
                tarea.observaciones or ""
            )

            self.tree.insert("", "end", values=values)

            if tarea.terminado:
                completadas += 1

        total = len(self.tareas)
        pendientes = total - completadas

        self.meter.configure(amountused=completadas, amounttotal=total if total > 0 else 1)
        self.pending_meter.configure(amountused=pendientes, amounttotal=total if total > 0 else 1)

    def abrir_formulario(self):
        ventana = tk.Toplevel(self)
        ventana.title("Agregar Tarea")
        ventana.geometry("550x400")

        nombre_var = StringVar()
        acciones_var = StringVar()
        fecha_inicio_entry = DateEntry(ventana, width=20, dateformat="%d-%m-%Y")
        plazo_entry = DateEntry(ventana, width=20, dateformat="%d-%m-%Y")


        Label(ventana, text="Tarea").grid(row=0, column=0, sticky="e", padx=10, pady=5)
        Entry(ventana, textvariable=nombre_var, width=40).grid(row=0, column=1, sticky="w")

        Label(ventana, text="Acciones a Realizar").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        Entry(ventana, textvariable=acciones_var, width=60).grid(row=1, column=1, sticky="w")

        Label(ventana, text="F. Inicio").grid(row=2, column=0, sticky="e", padx=10, pady=5)
        fecha_inicio_entry.grid(row=2, column=1, sticky="w")

        Label(ventana, text="Plazo").grid(row=3, column=0, sticky="e", padx=10, pady=5)
        plazo_entry.grid(row=3, column=1, sticky="w")

        Label(ventana, text="Observaciones").grid(row=4, column=0, sticky="ne", padx=10, pady=5)
        observaciones_text = tk.Text(ventana, width=40, height=4, wrap="word")
        observaciones_text.grid(row=4, column=1, sticky="w", pady=5)

        def guardar():
            tarea = Tarea(
                id=None,
                estado="Pendiente",
                nombre=nombre_var.get().strip(),
                compromiso=acciones_var.get().strip(),
                terminado=0,
                delegada=0,
                fecha_inicio=fecha_inicio_entry.entry.get(),
                plazo=plazo_entry.entry.get(),
                fecha_realizacion="",
                observaciones=observaciones_text.get("1.0", "end").strip()
            )
            try:
                tarea_id = agregar_tarea(tarea)
                tarea.id = tarea_id
                self.cargar_tareas()
                exportar_a_excel()
            except Exception as e:
                print(f"Error al guardar tarea: {e}")
            finally:
                ventana.destroy()

        Button(ventana, text="Guardar", style='MyCustom.TButton', command=guardar).grid(row=5, column=0, columnspan=2, pady=15)


    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        col_index = int(col.replace("#", "")) - 1

        if row_id and col_index in [4, 5]:
            idx = self.tree.index(row_id)
            tarea = self.tareas[idx]

            if col_index == 4:  # Terminado
                tarea.terminado = 0 if tarea.terminado else 1
            elif col_index == 5:  # Delegada
                tarea.delegada = 0 if tarea.delegada else 1

            tarea.estado = "Terminada" if tarea.terminado else "Pendiente"
            tarea.fecha_realizacion = datetime.today().strftime('%Y-%m-%d') if (tarea.terminado or tarea.delegada) else ""

            actualizar_tarea(tarea)
            self.cargar_tareas()

    def on_tree_doble_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = self.tree.identify_column(event.x)
        col_index = int(col.replace("#", "")) - 1

        # Evita abrir detalle si fue clic en columna de checkbox
        if col_index in [4, 5]:  # columnas "Terminado" y "Delegada"
            return

        self.ver_detalle()

    def ver_detalle(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Debe seleccionar una tarea para ver detalles.")
            return

        idx = self.tree.index(selected[0])
        tarea = self.tareas[idx]

        ventana = tk.Toplevel(self)
        ventana.title("Detalle de la Tarea")
        ventana.geometry("500x550")  # Aumentado el alto para que quepa todo

        Label(ventana, text="Tarea:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        text_tarea = tk.Text(ventana, height=3, wrap="word")
        text_tarea.pack(fill="both", expand=False, padx=10, pady=5)
        text_tarea.insert("1.0", tarea.nombre or "")
        text_tarea.configure(state="disabled")

        Label(ventana, text="Acciones a Realizar:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        text_acciones = tk.Text(ventana, height=6, wrap="word")
        text_acciones.pack(fill="both", expand=False, padx=10, pady=5)
        text_acciones.insert("1.0", tarea.compromiso or "")
        text_acciones.configure(state="disabled")

        # ✅ Observaciones
        Label(ventana, text="Observaciones:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        text_observaciones = tk.Text(ventana, height=4, wrap="word")
        text_observaciones.pack(fill="both", expand=True, padx=10, pady=5)
        text_observaciones.insert("1.0", tarea.observaciones or "")
        text_observaciones.configure(state="disabled")

        Button(ventana, text="Cerrar", style='MyCustom.TButton', command=ventana.destroy).pack(pady=10)

        


    def eliminar_tarea(self):
        selected = self.tree.selection()
        if selected:
            idx = self.tree.index(selected[0])
            tarea = self.tareas[idx]
            eliminar_tarea(tarea.id)
            self.cargar_tareas()

    def editar_tarea(self):
            selected = self.tree.selection()
            if not selected:
                tk.messagebox.showwarning("Advertencia", "Debe seleccionar una tarea para editar.")
                return

            idx = self.tree.index(selected[0])
            tarea = self.tareas[idx]

            ventana = tk.Toplevel(self)
            ventana.title("Editar Tarea")
            ventana.geometry("600x400")

            tarea_var = StringVar(value=tarea.nombre)
            plazo_var = StringVar(value=tarea.plazo)

            Label(ventana, text="Tarea").grid(row=0, column=0, sticky="e", padx=10, pady=5)
            Entry(ventana, textvariable=tarea_var, width=50).grid(row=0, column=1, sticky="w")

            Label(ventana, text="Acciones a Realizar").grid(row=1, column=0, sticky="ne", padx=10, pady=5)
            acciones_text = tk.Text(ventana, width=50, height=5, wrap="word")
            acciones_text.grid(row=1, column=1, sticky="w", pady=5)
            acciones_text.insert("1.0", tarea.compromiso or "")

            Label(ventana, text="Plazo").grid(row=2, column=0, sticky="e", padx=10, pady=5)
            Entry(ventana, textvariable=plazo_var, width=30).grid(row=2, column=1, sticky="w")

            Label(ventana, text="Observaciones").grid(row=3, column=0, sticky="ne", padx=10, pady=5)
            observaciones_text = tk.Text(ventana, width=50, height=5, wrap="word")
            observaciones_text.grid(row=3, column=1, sticky="w", pady=5)
            observaciones_text.insert("1.0", tarea.observaciones or "")

            def guardar_edicion():
                tarea.nombre = tarea_var.get().strip()
                tarea.compromiso = acciones_text.get("1.0", "end").strip()
                tarea.plazo = plazo_var.get().strip()
                tarea.observaciones = observaciones_text.get("1.0", "end").strip()

                try:
                    actualizar_tarea(tarea)
                    self.cargar_tareas()
                except Exception as e:
                    print(f"Error al editar tarea: {e}")
                finally:
                    ventana.destroy()

            Button(ventana, text="Guardar", style='MyCustom.TButton', command=guardar_edicion).grid(row=4, column=0, columnspan=2, pady=15)


    def importar_tareas_desde_excel(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx")]
        )
        if not archivo:
            return

        try:
            wb = openpyxl.load_workbook(archivo)
            hoja = wb.active
            filas_agregadas = 0

            for fila in hoja.iter_rows(min_row=2, values_only=True):  # Omitir encabezado
                if not fila or all(c is None for c in fila):
                    continue  # Saltar filas vacías

                datos = list(fila) + [None] * (9 - len(fila))  # Rellenar hasta 9 columnas

                from datetime import datetime

                def formatear_fecha(fecha):
                    if not fecha:
                        return ""
                    if isinstance(fecha, datetime):
                        return fecha.strftime("%Y-%m-%d")
                    try:
                        partes = str(fecha).strip().split()
                        return partes[0] if partes else ""
                    except Exception:
                        return ""

                try:
                    tarea = Tarea(
                        id=None,
                        estado=datos[0] or "",
                        nombre=datos[1] or "",
                        compromiso=datos[2] or "",
                        terminado=int(datos[3]) if datos[3] is not None else 0,
                        delegada=int(datos[4]) if datos[4] is not None else 0,
                        fecha_inicio=formatear_fecha(datos[5]),
                        plazo=formatear_fecha(datos[6]),
                        fecha_realizacion=formatear_fecha(datos[7]),
                        observaciones=datos[8] or ""
                    )
                    db.agregar_tarea(tarea)
                    filas_agregadas += 1
                except Exception as e:
                    print(f"Error al importar fila: {fila}\n{e}")
                    continue

            messagebox.showinfo("Importación completa", f"Se importaron {filas_agregadas} tareas.")
            self.cargar_tareas()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar el archivo:\n{e}")




