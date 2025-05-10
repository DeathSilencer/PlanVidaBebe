import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
import datetime
import os
import sys

from PIL import Image, ImageTk
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Importar nuestras clases y funciones de los módulos creados
from modules.models import Gasto, Etapa, PlanVida, Ingreso
from modules import db_handler
from modules.finances import evaluar_inversion
from modules.family_support import total_apoyo, agregar_recurso
from modules.time_management import generar_cronograma_financiero
from modules.home_expenses import HomeExpense
from modules.baby_expenses import BabyExpense
from modules.hospital_postpartum import HospitalExpense
from modules.documentation_events import EventExpense
from modules.services import ServiceExpense
from modules.family_organization import planificar_horarios

# Aseguramos que existan las carpetas necesarias
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists("images"):
    os.makedirs("images")

# Inicializamos la base de datos
db_handler.init_db()

# Creamos un objeto global para el plan de vida con etapas predefinidas
plan_vida = PlanVida()
predefined_stages = [
    ("Embarazo", 9),
    ("Nacimiento", 1),
    ("Primer Año", 12),
    ("Segundo Año", 12),
    ("Tercer Año", 12),
    ("Cuarto Año", 12),
    ("Quinto Año", 12)
]
for nombre, duracion in predefined_stages:
    etapa = Etapa(nombre, duracion)
    plan_vida.agregar_etapa(etapa)

def cargar_gastos():
    """Carga los gastos desde la base de datos y los asigna al objeto plan_vida."""
    from modules.db_handler import obtener_gastos
    datos = obtener_gastos()  # Devuelve una lista de filas
    if datos:
        for row in datos:
            # row tiene la estructura: [id, categoria, monto, periodicidad, fecha, etapa, origen]
            categoria, monto, periodicidad, fecha, etapa_nombre = row[1], row[2], row[3], row[4], row[5]
            # Creamos el objeto Gasto
            gasto = Gasto(categoria, monto, periodicidad, fecha, etapa_nombre)
            etapa_normalizada = etapa_nombre.strip().lower()
            for e in plan_vida.etapas:
                if e.nombre.strip().lower() == etapa_normalizada:
                    e.agregar_gasto(gasto)
                    break

# Cargamos los gastos previamente guardados para que el resumen no se reinicie
cargar_gastos()

# ---------- Funciones extras para las gráficas adicionales ----------
def simulate_inversion(initial, monthly, rate, term):
    """Calcula el valor acumulado mes a mes usando interés compuesto."""
    values = []
    total = initial
    monthly_rate = (1 + rate) ** (1/12) - 1
    for _ in range(term):
        total = total * (1 + monthly_rate) + monthly
        values.append(total)
    return values

def plot_cronograma_financiero_tk(parent, df):
    """Genera una gráfica de líneas con la evolución de Gastos, Ingresos y Balance."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df["Mes"], df["Gastos"], marker='o', label="Gastos")
    ax.plot(df["Mes"], df["Ingresos"], marker='o', label="Ingresos")
    ax.plot(df["Mes"], df["Balance"], marker='o', label="Balance")
    ax.set_title("Evolución del Cronograma Financiero (60 meses)")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Monto (MXN)")
    ax.legend()
    ax.grid(True)
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack()

def plot_inversion_comparativa_tk(parent, initial, monthly, term):
    """Genera una gráfica comparativa de inversión para tasas del 6% y 12%."""
    months = list(range(1, term+1))
    values_6 = simulate_inversion(initial, monthly, 0.06, term)
    values_12 = simulate_inversion(initial, monthly, 0.12, term)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(months, values_6, marker='o', label="6% Anual")
    ax.plot(months, values_12, marker='o', label="12% Anual")
    ax.set_title("Comparación de Proyección de Inversión")
    ax.set_xlabel("Meses")
    ax.set_ylabel("Valor Acumulado (MXN)")
    ax.legend()
    ax.grid(True)
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack()

# ---------------------- Clases del Programa ---------------------------
class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Plan de Vida del Bebé")
        self.state("zoomed")
        self.fullscreen = True
        self.geometry("900x700")
        self.attributes("-fullscreen", self.fullscreen)
        self.center_window()
        # Vincula F11 para alternar pantalla completa
        self.bind("<F11>", self.toggle_fullscreen)
        # Vincula el protocolo de cierre para salir completamente
        self.protocol("WM_DELETE_WINDOW", self.on_closing)        

        # Estilo TTK
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Infantil.TButton", font=("Comic Sans MS", 12), foreground="#444444")
        style.configure("TNotebook.Tab", font=("Comic Sans MS", 11), padding=[5, 2])

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Cargar íconos
        self.icon_register = self.load_icon("icon_register.png", (40, 40))
        self.icon_reports = self.load_icon("icon_reports.png", (40, 40))
        self.icon_simulation = self.load_icon("icon_simulation.png", (40, 40))
        self.icon_income = self.load_icon("icon_income.png", (40, 40))
        self.icon_extras = self.load_icon("icon_extras.png", (40, 40))
        self.icon_back = self.load_icon("icon_back.png", (25, 25))
        self.icon_exit = self.load_icon("icon_exit.png", (40, 40))

        self.frames = {}
        for F in (HomePage, RegisterExpensePage, ReportPage, SimulationPage, IncomePage, ModulesPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(HomePage)

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)
        
    def on_closing(self):
        if messagebox.askokcancel("Salir", "¿Desea salir de la aplicación?"):
            self.destroy()
            import sys
            sys.exit()

    def load_icon(self, filename, size):
        path = os.path.join("images", filename)
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path)
            img = img.resize(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error cargando ícono {filename}: {e}")
            return None

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
        self.center_window()

# -------------------- Página de Inicio --------------------
class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # 1) Cargamos la imagen original (sin reescalar)
        self.original_bg = None
        try:
            path_bg = os.path.join("images", "Fondo1.jpg")
            self.original_bg = Image.open(path_bg)
        except Exception as e:
            print("Error cargando fondo HomePage:", e)

        # 2) Creamos un Label para el fondo y lo colocamos con relwidth=1 y relheight=1
        self.bg_label = tk.Label(self)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # 3) Vinculamos el evento <Configure> para redimensionar cuando cambie el tamaño
        self.bind("<Configure>", self._resize_bg)

        title_label = tk.Label(self, text="Bienvenido a Plan de Vida del Bebé",
                               font=("Comic Sans MS", 28), fg="#2E86C1", bg="#FFFB8E")
        title_label.pack(pady=50)

        btn_frame = tk.Frame(self, bg="#FFFB8E")
        btn_frame.pack(pady=30)

        btn_register = ttk.Button(btn_frame, text="Registrar Gasto",
                                  image=self.controller.icon_register,
                                  compound="left",
                                  style="Infantil.TButton",
                                  command=lambda: self.controller.show_frame(RegisterExpensePage))
        btn_register.pack(pady=5)

        btn_report = ttk.Button(btn_frame, text="Ver Reportes",
                                image=self.controller.icon_reports,
                                compound="left",
                                style="Infantil.TButton",
                                command=lambda: self.controller.show_frame(ReportPage))
        btn_report.pack(pady=5)

        btn_income = ttk.Button(btn_frame, text="Registrar Ingreso",
                                image=self.controller.icon_income,
                                compound="left",
                                style="Infantil.TButton",
                                command=lambda: self.controller.show_frame(IncomePage))
        btn_income.pack(pady=5)

        btn_extras = ttk.Button(btn_frame, text="Módulos Extras",
                                image=self.controller.icon_extras,
                                compound="left",
                                style="Infantil.TButton",
                                command=lambda: self.controller.show_frame(ModulesPage))
        btn_extras.pack(pady=5)

        btn_simulation = ttk.Button(btn_frame, text="Simulaciones y Escenarios",
                                image=self.controller.icon_simulation,
                                compound="left",
                                style="Infantil.TButton",
                                command=lambda: self.controller.show_frame(SimulationPage))
        btn_simulation.pack(pady=5)
        
                # Botón de salida
        btn_exit = ttk.Button(btn_frame, text="Salir", 
                                image=self.controller.icon_exit,
                                compound="left",
                                style="Infantil.TButton", 
                                command=self.controller.on_closing)
        btn_exit.pack(pady=5)
        
    def _resize_bg(self, event):
        """
        Redimensiona la imagen de fondo cada vez que el Frame cambie de tamaño.
        """
        # Si no cargó la imagen o la ventana está muy pequeña, no hacemos nada
        if not self.original_bg:
            return

        new_width = event.width
        new_height = event.height
        if new_width < 10 or new_height < 10:
            return

        # Redimensionamos la imagen original al nuevo tamaño
        resized_image = self.original_bg.resize((new_width, new_height), Image.LANCZOS)

        # Creamos un nuevo PhotoImage y actualizamos el Label
        self.bg_image = ImageTk.PhotoImage(resized_image)
        self.bg_label.config(image=self.bg_image)

# -------------------- Registro de Gastos --------------------
class RegisterExpensePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Fondo para RegisterExpensePage
        self.original_bg = None
        try:
            path_bg = os.path.join("images", "Fondo2.jpg")
            self.original_bg = Image.open(path_bg)
        except Exception as e:
            print("Error cargando fondo RegisterExpensePage:", e)
        self.bg_label = tk.Label(self)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._resize_bg)

        title_label = tk.Label(self, text="Registrar Nuevo Gasto",
                               font=("Comic Sans MS", 24), fg="#27AE60", bg="#FFF3A1")
        title_label.pack(pady=20)

        form_frame = tk.Frame(self, bg="#FFF3A1")
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Categoría:", bg="#FFF3A1").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.combo_categoria = ttk.Combobox(form_frame, values=[
            "Chequeos Prenatales",
            "Parto Natural",
            "Seguro Médico (Madre y bebé)",
            "Seguro Médico (Bebé)",
            "Vacunas",
            "Consultas Pediátricas",
            "Urgencias Médicas",
            "Pañales",
            "Fórmula Infantil y Leche de 400g",
            "Alimentos del bebé",
            "Productos de Higiene",
            "Mobiliario Básico",
            "Ropa 0-12 Meses",
            "Ropa 1-5 Años",
            "Guardería Pública",
            "Guardería Privada",
            "Educación Preescolar Pública",
            "Educación Preescolar Privada",
            "Juguetes y Libros",
            "Actividades Recreativas",
            "Transporte para Actividades",
            "Servicios del Hogar",
            "Vivienda y Adaptaciones",
            "Alimentación del Hogar",
            "Comunicación y Telefonía",
            "Otros Gastos Familiares"
        ], width=50)
        self.combo_categoria.current(0)
        self.combo_categoria.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Monto (MXN):", bg="#FFF3A1").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_monto = tk.Entry(form_frame)
        self.entry_monto.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Periodicidad:", bg="#FFF3A1").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.combo_periodicidad = ttk.Combobox(form_frame, values=["único", "mensual", "anual"])
        self.combo_periodicidad.current(0)
        self.combo_periodicidad.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Fecha (YYYY-MM-DD):", bg="#FFF3A1").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_fecha = tk.Entry(form_frame)
        self.entry_fecha.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Etapa:", bg="#FFF3A1").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.combo_etapa = ttk.Combobox(form_frame, values=[e[0] for e in predefined_stages])
        self.combo_etapa.current(0)
        self.combo_etapa.grid(row=4, column=1, padx=5, pady=5)

        btn_add = ttk.Button(self, text="Agregar Gasto", style="Infantil.TButton", command=self.agregar_gasto)
        btn_add.pack(pady=10)

        btn_volver = ttk.Button(self, text="Volver al Inicio", image=self.controller.icon_back,
                                compound="left", style="Infantil.TButton",
                                command=lambda: self.controller.show_frame(HomePage))
        btn_volver.pack(pady=5)


    def _resize_bg(self, event):
        if not self.original_bg:
            return
        new_width = event.width
        new_height = event.height
        if new_width < 10 or new_height < 10:
            return
        resized_image = self.original_bg.resize((new_width, new_height), Image.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(resized_image)
        self.bg_label.config(image=self.bg_image)

    def agregar_gasto(self):
        # Se obtiene la información del formulario
        categoria = self.combo_categoria.get()
        try:
            monto = float(self.entry_monto.get())
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número.")
            return
        periodicidad = self.combo_periodicidad.get()
        fecha = self.entry_fecha.get()
        try:
            datetime.datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "La fecha debe tener formato YYYY-MM-DD.")
            return
        etapa = self.combo_etapa.get()

        # Se crea el objeto Gasto
        nuevo_gasto = Gasto(categoria, monto, periodicidad, fecha, etapa)
        from modules.db_handler import insertar_gasto
        insertar_gasto(categoria, monto, periodicidad, fecha, etapa, origen="general")

        # Se agrega el gasto a la etapa correspondiente en plan_vida
        agregado = False
        etapa_normalizada = etapa.strip().lower()
        for e in plan_vida.etapas:
            if e.nombre.strip().lower() == etapa_normalizada:
                e.agregar_gasto(nuevo_gasto)
                agregado = True
                print(f"Gasto agregado a la etapa: {e.nombre}")
                break

        if not agregado:
            print("No se encontró la etapa correspondiente para agregar el gasto.")
            messagebox.showwarning("Atención", "El gasto no se asoció a ninguna etapa. Verifica que la etapa seleccionada coincida con la definida en el plan de vida.")

        messagebox.showinfo("Éxito", "Gasto registrado exitosamente.")

        # Limpiar los campos del formulario
        self.entry_monto.delete(0, tk.END)
        self.entry_fecha.delete(0, tk.END)
        self.combo_periodicidad.current(0)
        self.combo_etapa.current(0)

# -------------------- Reporte de Gastos --------------------
class ReportPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Fondo para ReportPage
        self.original_bg = None
        try:
            path_bg = os.path.join("images", "Fondo3.jpg")
            self.original_bg = Image.open(path_bg)
        except Exception as e:
            print("Error cargando fondo ReportPage:", e)
        self.bg_label = tk.Label(self)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._resize_bg)

        # Contenedor superior para controles
        control_frame = tk.Frame(self, bg="#FEC736")
        control_frame.pack(fill="x", padx=10, pady=5)

        title = tk.Label(control_frame, text="Reportes y Gráficos", font=("Comic Sans MS", 24),
                         fg="#8E44AD", bg="#FEC736")
        title.pack(pady=5)

        btn_actualizar = ttk.Button(control_frame, text="Actualizar Reporte de Gastos",
                                      style="Infantil.TButton", command=self.generar_reporte)
        btn_actualizar.pack(side="left", padx=5, pady=5)

        btn_reporte_ingresos = ttk.Button(control_frame, text="Mostrar Reporte de Ingresos",
                                          style="Infantil.TButton", command=self.generar_reporte_ingresos)
        btn_reporte_ingresos.pack(side="left", padx=5, pady=5)

        btn_export_excel = ttk.Button(control_frame, text="Exportar a Excel",
                                      style="Infantil.TButton", command=self.exportar_excel)
        btn_export_excel.pack(side="left", padx=5, pady=5)

        btn_export_pdf = ttk.Button(control_frame, text="Exportar a PDF",
                                    style="Infantil.TButton", command=self.exportar_pdf)
        btn_export_pdf.pack(side="left", padx=5, pady=5)

        btn_borrar_todos = ttk.Button(control_frame, text="Borrar Todos los Datos",
                                      style="Infantil.TButton", command=self.borrar_datos)
        btn_borrar_todos.pack(side="left", padx=5, pady=5)

        btn_borrar_especifico = ttk.Button(control_frame, text="Borrar Registro Específico",
                                          style="Infantil.TButton", command=self.borrar_dato_especifico)
        btn_borrar_especifico.pack(side="left", padx=5, pady=5)

        # Contenedor scrollable para el reporte
        container = tk.Frame(self, bg="#ffffff")
        container.pack(fill="both", expand=True, padx=10, pady=5)
        canvas = tk.Canvas(container, bg="#ffffff")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.report_frame = tk.Frame(canvas, bg="#ffffff")
        self.report_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.report_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_volver = ttk.Button(self, text="Volver al Inicio", image=self.controller.icon_back,
                                compound="left", style="Infantil.TButton",
                                command=lambda: self.controller.show_frame(HomePage))
        btn_volver.pack(pady=5)

    def borrar_datos(self):
        from modules.db_handler import borrar_todos_los_datos
        if messagebox.askyesno("Confirmar", "¿Seguro que deseas borrar TODOS los datos?"):
            borrar_todos_los_datos()
            messagebox.showinfo("Éxito", "Datos borrados correctamente.")
            self.generar_reporte()

    def borrar_dato_especifico(self):
        from modules.db_handler import obtener_gastos, borrar_datos_por_id
        datos = obtener_gastos()
        if not datos:
            messagebox.showinfo("Sin Datos", "No hay datos para borrar.")
            return
        top = tk.Toplevel(self)
        top.title("Borrar un Registro")
        top.geometry("400x150")
        tk.Label(top, text="Selecciona el registro a borrar:").pack(pady=10)
        items = [f"{row[0]} - {row[1]} - ${row[2]}" for row in datos]
        combo = ttk.Combobox(top, values=items, width=50)
        combo.pack(pady=5)
        def confirmar_borrar():
            seleccionado = combo.get()
            if seleccionado:
                try:
                    record_id = int(seleccionado.split(" - ")[0])
                except ValueError:
                    return
                borrar_datos_por_id(record_id)
                messagebox.showinfo("Éxito", "Registro borrado.")
                top.destroy()
                self.generar_reporte()
        btn_confirm = ttk.Button(top, text="Borrar", command=confirmar_borrar)
        btn_confirm.pack(pady=5)

    def _resize_bg(self, event):
        if not self.original_bg:
            return
        new_width = event.width
        new_height = event.height
        if new_width < 10 or new_height < 10:
            return
        resized_image = self.original_bg.resize((new_width, new_height), Image.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(resized_image)
        self.bg_label.config(image=self.bg_image)

    def generar_reporte(self):
        # 1) Limpiar el frame que contendrá el reporte
        for widget in self.report_frame.winfo_children():
            widget.destroy()

        from modules.db_handler import obtener_gastos
        datos = obtener_gastos()
        if not datos:
            tk.Label(self.report_frame, text="No hay datos para mostrar.", bg="#ffffff").pack()
            return

        # 2) Crear DataFrame con todos los gastos
        df = pd.DataFrame(datos, columns=["id", "categoria", "monto", 
                                      "periodicidad", "fecha", "etapa", "origen"])

        # 3) Añadir columna "cat_etapa" = "categoria (etapa)"
        df["cat_etapa"] = df["categoria"] + " (" + df["etapa"] + ")"

        # -- MOSTRAR DETALLE DE CADA ÍTEM --
        # 4) Mostramos cada fila (cat_etapa, monto) en un Text para no perder el detalle
        text = tk.Text(self.report_frame, height=10, width=100)
        text.insert(tk.END, df[["cat_etapa", "monto"]].to_string(index=False))
        text.pack(pady=5)

        # -- MOSTRAR RESUMEN POR ETAPA --
        # 5) Mostrar el resumen de cada etapa una sola vez
        resumen_etapas = "Resumen por Etapa:\n"
        for etapa_obj in plan_vida.etapas:
            resumen_etapas += f"{etapa_obj.nombre}: {etapa_obj.calcular_total_gastos():.2f} MXN\n"
        tk.Label(self.report_frame, text=resumen_etapas, font=("Arial", 10),
                justify="left", bg="#ffffff").pack(pady=5)

        # -- CREAR GRÁFICA AGRUPADA POR cat_etapa --
        # 6) Agrupamos para la gráfica (sumando los montos de cada cat_etapa)
        df_grafica = df.groupby("cat_etapa")["monto"].sum().reset_index()

        # 7) Generamos la gráfica con un tamaño mayor
        fig, ax = plt.subplots(figsize=(8, 6))  # Aumenta si quieres aún más grande
        ax.bar(df_grafica["cat_etapa"], df_grafica["monto"])
        ax.set_title("Gastos Totales por Categoría y Etapa")
        ax.set_xlabel("Categoría (Etapa)")
        ax.set_ylabel("MXN")

        # Ajustar las etiquetas para que no se encimen
        plt.xticks(rotation=45, ha="right")
        fig.tight_layout()

        # 8) Mostrar la gráfica en el Frame
        canvas_fig = FigureCanvasTkAgg(fig, master=self.report_frame)
        canvas_fig.draw()
        canvas_fig.get_tk_widget().pack(pady=5)




    def generar_reporte_ingresos(self):
        for widget in self.report_frame.winfo_children():
            widget.destroy()
        from modules.db_handler import obtener_ingresos
        datos = obtener_ingresos()
        if not datos:
            tk.Label(self.report_frame, text="No hay ingresos para mostrar.", bg="#ffffff").pack()
            return
        df = pd.DataFrame(datos, columns=["id", "tipo", "monto", "periodicidad", "fecha", "descripcion"])
        text = tk.Text(self.report_frame, height=10)
        text.insert(tk.END, df.to_string(index=False))
        text.pack(pady=5)

    def exportar_excel(self):
        from modules.db_handler import obtener_gastos
        datos = obtener_gastos()
        if not datos:
            messagebox.showinfo("Exportar", "No hay datos para exportar.")
            return
        df = pd.DataFrame(datos, columns=["id", "categoria", "monto", "periodicidad", "fecha", "etapa", "origen"])
        try:
            df.to_excel("reporte_plan_vida.xlsx", index=False)
            messagebox.showinfo("Exportar", "Reporte exportado a 'reporte_plan_vida.xlsx'")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def exportar_pdf(self):
        from modules.db_handler import obtener_gastos
        datos = obtener_gastos()
        if not datos:
            messagebox.showinfo("Exportar", "No hay datos para exportar.")
            return
        try:
            pdf_file = "reporte_plan_vida.pdf"
            c = canvas.Canvas(pdf_file, pagesize=letter)
            width, height = letter
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "Reporte del Plan de Vida del Bebé")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 80, "Reporte de gastos por categoría:")
            df = pd.DataFrame(datos, columns=["id", "categoria", "monto", "periodicidad", "fecha", "etapa", "origen"])
            resumen = df.groupby("categoria")["monto"].sum().reset_index()
            y = height - 110
            for index, row in resumen.iterrows():
                line = f"{row['categoria']}: {row['monto']} MXN"
                c.drawString(50, y, line)
                y -= 15
                if y < 50:
                    c.showPage()
                    y = height - 50
            c.save()
            messagebox.showinfo("Exportar", f"Reporte exportado a '{pdf_file}'")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el PDF: {e}")

# -------------------- Simulaciones y Escenarios --------------------
class SimulationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.inversion_params = {
            "initial": 10000,
            "monthly": 2000,
            "term": 60,
            "rate": 0.06
        }
        self.cronograma_params = {
            "gastos_inicial": 10000,
            "gastos_final": 60000,
            "ingresos_inicial": 15000,
            "ingresos_final": 70000,
            "term": 60
        }
        # Fondo para SimulationPage
        self.original_bg = None
        try:
            path_bg = os.path.join("images", "Fondo2.jpg")
            self.original_bg = Image.open(path_bg)
        except Exception as e:
            print("Error cargando fondo SimulationPage:", e)
        self.bg_label = tk.Label(self)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._resize_bg)

        title_label = tk.Label(self, text="Simulaciones y Escenarios",
                               font=("Comic Sans MS", 24), fg="#D35400", bg="#FFF3A1")
        title_label.pack(pady=10)
        
        notebook = ttk.Notebook(self)
        notebook.pack(pady=5, fill="both", expand=True)

        # Pestaña: Distribución de Horas
        self.time_frame = tk.Frame(notebook)
        notebook.add(self.time_frame, text="Distribución de Horas")
        tk.Label(self.time_frame, text="Horas de sueño (por día):").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.entry_sleep = tk.Entry(self.time_frame)
        self.entry_sleep.grid(row=0, column=1, padx=5, pady=3)
        tk.Label(self.time_frame, text="Horas de trabajo:").grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.entry_work = tk.Entry(self.time_frame)
        self.entry_work.grid(row=1, column=1, padx=5, pady=3)
        tk.Label(self.time_frame, text="Horas de estudio:").grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.entry_study = tk.Entry(self.time_frame)
        self.entry_study.grid(row=2, column=1, padx=5, pady=3)
        tk.Label(self.time_frame, text="Horas de cuidado del bebé:").grid(row=3, column=0, sticky="e", padx=5, pady=3)
        self.entry_care = tk.Entry(self.time_frame)
        self.entry_care.grid(row=3, column=1, padx=5, pady=3)
        tk.Label(self.time_frame, text="Otras horas:").grid(row=4, column=0, sticky="e", padx=5, pady=3)
        self.entry_other = tk.Entry(self.time_frame)
        self.entry_other.grid(row=4, column=1, padx=5, pady=3)
        btn_time_chart = ttk.Button(self.time_frame, text="Generar Gráfica de Distribución de Horas",
                                    style="Infantil.TButton", command=self.generate_time_chart)
        btn_time_chart.grid(row=5, column=0, columnspan=2, pady=10)
        self.time_chart_frame = tk.Frame(self.time_frame)
        self.time_chart_frame.grid(row=6, column=0, columnspan=2)

        # Pestaña: Simulaciones Avanzadas
        self.advanced_frame = tk.Frame(notebook, bg="#F7F7F7")
        notebook.add(self.advanced_frame, text="Simulaciones Avanzadas")
        adv_control_frame = tk.Frame(self.advanced_frame, bg="#F7F7F7")
        adv_control_frame.pack(fill="x", padx=10, pady=10)
        btn_edit_sim = ttk.Button(adv_control_frame, text="Editar Simuladores",
                                  style="Infantil.TButton", command=self.editar_simulaciones)
        btn_edit_sim.pack(side="left", padx=5, pady=5)
        btn_graph_cron = ttk.Button(adv_control_frame, text="Mostrar Gráfica Cronograma",
                                    style="Infantil.TButton", command=self.mostrar_grafica_cronograma)
        btn_graph_cron.pack(side="left", padx=5, pady=5)
        btn_graph_inver = ttk.Button(adv_control_frame, text="Mostrar Gráfica Inversión",
                                     style="Infantil.TButton", command=self.mostrar_grafica_inversion)
        btn_graph_inver.pack(side="left", padx=5, pady=5)
        self.advanced_graph_frame = tk.Frame(self.advanced_frame, bg="#F7F7F7")
        self.advanced_graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        btn_volver = ttk.Button(self, text="Volver al Inicio", image=self.controller.icon_back,
                                compound="left", style="Infantil.TButton",
                                command=lambda: self.controller.show_frame(HomePage))
        btn_volver.pack(pady=5)


    def _resize_bg(self, event):
        if not self.original_bg:
            return
        new_width = event.width
        new_height = event.height
        if new_width < 10 or new_height < 10:
            return
        resized_image = self.original_bg.resize((new_width, new_height), Image.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(resized_image)
        self.bg_label.config(image=self.bg_image)

    def generate_time_chart(self):
        try:
            sleep = float(self.entry_sleep.get())
            work = float(self.entry_work.get())
            study = float(self.entry_study.get())
            care = float(self.entry_care.get())
            other = float(self.entry_other.get())
        except ValueError:
            messagebox.showerror("Error", "Ingresa valores numéricos para las horas.")
            return
        total = sleep + work + study + care + other
        if total > 24:
            messagebox.showerror("Error", "La suma de horas no puede superar 24.")
            return
        labels = ["Sueño", "Trabajo", "Estudio", "Cuidado del Bebé", "Otros"]
        values = [sleep, work, study, care, other]
        for widget in self.time_chart_frame.winfo_children():
            widget.destroy()
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(values, labels=labels, autopct="%1.1f%%")
        ax.set_title("Distribución de Horas Diarias")
        canvas = FigureCanvasTkAgg(fig, master=self.time_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def editar_simulaciones(self):
        editor = tk.Toplevel(self)
        editor.title("Editar Simulaciones")
        editor.geometry("400x400")
        # Sección de Inversión
        inv_frame = tk.LabelFrame(editor, text="Simulación de Inversión", padx=10, pady=10)
        inv_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(inv_frame, text="Inversión Inicial (MXN):").grid(row=0, column=0, sticky="w")
        entry_initial = tk.Entry(inv_frame)
        entry_initial.insert(0, str(self.inversion_params["initial"]))
        entry_initial.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(inv_frame, text="Aporte Mensual (MXN):").grid(row=1, column=0, sticky="w")
        entry_monthly = tk.Entry(inv_frame)
        entry_monthly.insert(0, str(self.inversion_params["monthly"]))
        entry_monthly.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(inv_frame, text="Tasa de Interés Anual (%):").grid(row=2, column=0, sticky="w")
        entry_rate = tk.Entry(inv_frame)
        entry_rate.insert(0, str(self.inversion_params["rate"] * 100))
        entry_rate.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(inv_frame, text="Plazo (meses):").grid(row=3, column=0, sticky="w")
        entry_term = tk.Entry(inv_frame)
        entry_term.insert(0, str(self.inversion_params["term"]))
        entry_term.grid(row=3, column=1, padx=5, pady=5)
        # Sección de Cronograma
        cron_frame = tk.LabelFrame(editor, text="Simulación de Cronograma", padx=10, pady=10)
        cron_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(cron_frame, text="Gastos Inicial (MXN):").grid(row=0, column=0, sticky="w")
        entry_gastos_ini = tk.Entry(cron_frame)
        entry_gastos_ini.insert(0, str(self.cronograma_params["gastos_inicial"]))
        entry_gastos_ini.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(cron_frame, text="Gastos Final (MXN):").grid(row=1, column=0, sticky="w")
        entry_gastos_fin = tk.Entry(cron_frame)
        entry_gastos_fin.insert(0, str(self.cronograma_params["gastos_final"]))
        entry_gastos_fin.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(cron_frame, text="Ingresos Inicial (MXN):").grid(row=2, column=0, sticky="w")
        entry_ingresos_ini = tk.Entry(cron_frame)
        entry_ingresos_ini.insert(0, str(self.cronograma_params["ingresos_inicial"]))
        entry_ingresos_ini.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(cron_frame, text="Ingresos Final (MXN):").grid(row=3, column=0, sticky="w")
        entry_ingresos_fin = tk.Entry(cron_frame)
        entry_ingresos_fin.insert(0, str(self.cronograma_params["ingresos_final"]))
        entry_ingresos_fin.grid(row=3, column=1, padx=5, pady=5)
        def aplicar_cambios():
            try:
                self.inversion_params["initial"] = float(entry_initial.get())
                self.inversion_params["monthly"] = float(entry_monthly.get())
                self.inversion_params["rate"] = float(entry_rate.get()) / 100
                self.inversion_params["term"] = int(entry_term.get())
                self.cronograma_params["gastos_inicial"] = float(entry_gastos_ini.get())
                self.cronograma_params["gastos_final"] = float(entry_gastos_fin.get())
                self.cronograma_params["ingresos_inicial"] = float(entry_ingresos_ini.get())
                self.cronograma_params["ingresos_final"] = float(entry_ingresos_fin.get())
                self.cronograma_params["term"] = int(entry_term.get())
                messagebox.showinfo("Éxito", "Parámetros actualizados correctamente.")
                editor.destroy()
            except Exception as ex:
                messagebox.showerror("Error", f"Verifica los valores ingresados: {ex}")
        btn_aplicar = ttk.Button(editor, text="Aplicar Cambios", style="Infantil.TButton", command=aplicar_cambios)
        btn_aplicar.pack(pady=10)

    def simulate_inversion(self, initial, monthly, rate, term):
        values = []
        total = initial
        monthly_rate = (1 + rate) ** (1/12) - 1
        for _ in range(term):
            total = total * (1 + monthly_rate) + monthly
            values.append(total)
        return values

    def mostrar_grafica_cronograma(self):
        for widget in self.advanced_graph_frame.winfo_children():
            widget.destroy()
        term = self.cronograma_params["term"]
        gastos = np.linspace(self.cronograma_params["gastos_inicial"],
                             self.cronograma_params["gastos_final"], term)
        ingresos = np.linspace(self.cronograma_params["ingresos_inicial"],
                               self.cronograma_params["ingresos_final"], term)
        df = pd.DataFrame({
            "Mes": list(range(1, term + 1)),
            "Gastos": gastos,
            "Ingresos": ingresos
        })
        df["Balance"] = df["Ingresos"] - df["Gastos"]
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(df["Mes"], df["Gastos"], marker='o', label="Gastos")
        ax.plot(df["Mes"], df["Ingresos"], marker='o', label="Ingresos")
        ax.plot(df["Mes"], df["Balance"], marker='o', label="Balance")
        ax.set_title("Evolución del Cronograma Financiero")
        ax.set_xlabel("Mes")
        ax.set_ylabel("Monto (MXN)")
        ax.legend()
        ax.grid(True)
        canvas_fig = FigureCanvasTkAgg(fig, master=self.advanced_graph_frame)
        canvas_fig.draw()
        canvas_fig.get_tk_widget().pack(pady=5)

    def mostrar_grafica_inversion(self):
        for widget in self.advanced_graph_frame.winfo_children():
            widget.destroy()
        term = self.inversion_params["term"]
        initial = self.inversion_params["initial"]
        monthly = self.inversion_params["monthly"]
        rate = self.inversion_params["rate"]
        months = list(range(1, term + 1))
        values_current = self.simulate_inversion(initial, monthly, rate, term)
        values_12 = self.simulate_inversion(initial, monthly, 0.12, term)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(months, values_current, marker='o', label=f"Tasa {rate*100:.1f}%")
        ax.plot(months, values_12, marker='o', label="Tasa 12%")
        ax.set_title("Comparación de Proyección de Inversión")
        ax.set_xlabel("Meses")
        ax.set_ylabel("Valor Acumulado (MXN)")
        ax.legend()
        ax.grid(True)
        canvas_fig = FigureCanvasTkAgg(fig, master=self.advanced_graph_frame)
        canvas_fig.draw()
        canvas_fig.get_tk_widget().pack(pady=5)

# -------------------- Registrar Ingresos --------------------
class IncomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#E8F6F3")
        title_label = tk.Label(self, text="Registrar Ingreso", font=("Comic Sans MS", 24),
                               fg="#27AE60", bg="#E8F6F3")
        title_label.pack(pady=20)
        form_frame = tk.Frame(self, bg="#E8F6F3")
        form_frame.pack(pady=10)
        tk.Label(form_frame, text="Tipo de Ingreso:", bg="#E8F6F3").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.combo_tipo = ttk.Combobox(form_frame, values=[
            "Aguinaldo", "Utilidades", "Fondo de Ahorro", "Herencia", "Regalo Familiar", "Otro"
        ])
        self.combo_tipo.current(0)
        self.combo_tipo.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Monto (MXN):", bg="#E8F6F3").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_monto = tk.Entry(form_frame)
        self.entry_monto.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Periodicidad:", bg="#E8F6F3").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.combo_periodicidad = ttk.Combobox(form_frame, values=["único", "mensual", "anual"])
        self.combo_periodicidad.current(0)
        self.combo_periodicidad.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Fecha (YYYY-MM-DD):", bg="#E8F6F3").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_fecha = tk.Entry(form_frame)
        self.entry_fecha.grid(row=3, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Descripción (opcional):", bg="#E8F6F3").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.entry_descripcion = tk.Entry(form_frame)
        self.entry_descripcion.grid(row=4, column=1, padx=5, pady=5)
        btn_add = ttk.Button(self, text="Agregar Ingreso", style="Infantil.TButton", command=self.agregar_ingreso)
        btn_add.pack(pady=10)
        btn_volver = ttk.Button(self, text="Volver al Inicio", image=self.controller.icon_back,
                                compound="left", style="Infantil.TButton",
                                command=lambda: self.controller.show_frame(HomePage))
        btn_volver.pack(pady=5)

    def agregar_ingreso(self):
        tipo = self.combo_tipo.get()
        try:
            monto = float(self.entry_monto.get())
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número.")
            return
        periodicidad = self.combo_periodicidad.get()
        fecha = self.entry_fecha.get()
        descripcion = self.entry_descripcion.get()
        try:
            datetime.datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "La fecha debe tener formato YYYY-MM-DD.")
            return
        nuevo_ingreso = Ingreso(tipo, monto, periodicidad, fecha, descripcion)
        from modules.db_handler import insertar_ingreso
        insertar_ingreso(tipo, monto, periodicidad, fecha, descripcion)
        messagebox.showinfo("Éxito", "Ingreso registrado exitosamente.")
        self.combo_tipo.current(0)
        self.entry_monto.delete(0, tk.END)
        self.entry_fecha.delete(0, tk.END)
        self.entry_descripcion.delete(0, tk.END)

# -------------------- Módulos Extras --------------------
class ModulesPage(tk.Frame):
    """
    Página que integra los módulos adicionales.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#DFF0D8")
        title = tk.Label(self, text="Módulos Extras", font=("Comic Sans MS", 26), fg="#31708F", bg="#DFF0D8")
        title.pack(pady=10)
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)
        # Apoyo Familiar
        self.support_tab = tk.Frame(self.nb, bg="#F7F7F7")
        self.nb.add(self.support_tab, text="Apoyo Familiar")
        self.setup_support_tab()
        # Gastos del Hogar
        self.home_exp_tab = tk.Frame(self.nb, bg="#F7F7F7")
        self.nb.add(self.home_exp_tab, text="Gastos del Hogar")
        self.setup_home_exp_tab()
        # Gastos del Bebé
        self.baby_exp_tab = tk.Frame(self.nb, bg="#F7F7F7")
        self.nb.add(self.baby_exp_tab, text="Gastos del Bebé")
        self.setup_baby_exp_tab()
        # Hospital/Postparto
        self.hosp_tab = tk.Frame(self.nb, bg="#F7F7F7")
        self.nb.add(self.hosp_tab, text="Hospital/Postparto")
        self.setup_hosp_tab()
        # Documentación y Eventos
        self.events_tab = tk.Frame(self.nb, bg="#F7F7F7")
        self.nb.add(self.events_tab, text="Documentación/ Eventos")
        self.setup_events_tab()
        # Servicios
        self.services_tab = tk.Frame(self.nb, bg="#F7F7F7")
        self.nb.add(self.services_tab, text="Servicios")
        self.setup_services_tab()
        # Gráficas Extras
        self.extra_graph_tab = tk.Frame(self.nb, bg="#F7F7F7")
        self.nb.add(self.extra_graph_tab, text="Gráficas Extras")
        self.setup_extra_graph_tab()
        btn_volver = ttk.Button(self, text="Volver al Inicio", image=self.controller.icon_back,
                                compound="left", style="Infantil.TButton",
                                command=lambda: self.controller.show_frame(HomePage))
        btn_volver.pack(pady=5)

    def setup_fin_tab(self):
        # Aquí se pueden agregar más módulos si es necesario
        pass

    def setup_support_tab(self):
        tk.Label(self.support_tab, text="Apoyo Familiar", font=("Comic Sans MS", 16), bg="#F7F7F7").pack(pady=5)
        frame = tk.Frame(self.support_tab, bg="#F7F7F7")
        frame.pack(pady=5)
        tk.Label(frame, text="Ingresa montos (MXN) separados por comas:", bg="#F7F7F7").pack(pady=3)
        self.mod_support_entry = tk.Entry(frame, width=50)
        self.mod_support_entry.pack(pady=3)
        btn_calc = ttk.Button(self.support_tab, text="Calcular Total", style="Infantil.TButton", command=self.calc_mod_support)
        btn_calc.pack(pady=5)
        self.mod_support_result = tk.Label(self.support_tab, text="", bg="#F7F7F7", font=("Arial", 12))
        self.mod_support_result.pack(pady=5)

    def calc_mod_support(self):
        try:
            montos = [float(x.strip()) for x in self.mod_support_entry.get().split(",") if x.strip()]
            total = total_apoyo(montos)
            self.mod_support_result.config(text=f"Total de Apoyo: {total:.2f} MXN")
        except Exception as e:
            messagebox.showerror("Error", "Verifica los valores ingresados.")

    def setup_cronogram_tab(self):
        tk.Label(self.cronogram_tab, text="Cronograma Financiero (60 meses)", font=("Comic Sans MS", 16), bg="#F7F7F7").pack(pady=5)
        df = generar_cronograma_financiero()
        self.mod_cronogram_text = tk.Text(self.cronogram_tab, width=80, height=15)
        self.mod_cronogram_text.insert(tk.END, df.to_string(index=False))
        self.mod_cronogram_text.pack(pady=5)

    def setup_home_exp_tab(self):
        tk.Label(self.home_exp_tab, text="Gastos del Hogar", font=("Comic Sans MS", 16), bg="#F7F7F7").pack(pady=5)
        frame = tk.Frame(self.home_exp_tab, bg="#F7F7F7")
        frame.pack(pady=5)
        tk.Label(frame, text="Nombre del gasto:", bg="#F7F7F7").grid(row=0, column=0, padx=5, pady=3)
        self.mod_home_name = tk.Entry(frame)
        self.mod_home_name.grid(row=0, column=1, padx=5, pady=3)
        tk.Label(frame, text="Monto (MXN):", bg="#F7F7F7").grid(row=1, column=0, padx=5, pady=3)
        self.mod_home_monto = tk.Entry(frame)
        self.mod_home_monto.grid(row=1, column=1, padx=5, pady=3)
        tk.Label(frame, text="Periodicidad:", bg="#F7F7F7").grid(row=2, column=0, padx=5, pady=3)
        self.mod_home_period = ttk.Combobox(frame, values=["único", "mensual", "anual"])
        self.mod_home_period.current(0)
        self.mod_home_period.grid(row=2, column=1, padx=5, pady=3)
        btn_calc = ttk.Button(self.home_exp_tab, text="Calcular Gasto Anual", style="Infantil.TButton", command=self.calc_mod_home)
        btn_calc.pack(pady=5)
        self.mod_home_result = tk.Label(self.home_exp_tab, text="", bg="#F7F7F7", font=("Arial", 12))
        self.mod_home_result.pack(pady=5)

    def calc_mod_home(self):
        try:
            name = self.mod_home_name.get()
            monto = float(self.mod_home_monto.get())
            periodicidad = self.mod_home_period.get()
            expense = HomeExpense(name, monto, periodicidad)
            total = expense.total(12)
            self.mod_home_result.config(text=f"Gasto Anual: {total:.2f} MXN")
            from modules.db_handler import insertar_gasto
            insertar_gasto(name, monto, periodicidad, datetime.date.today().strftime("%Y-%m-%d"), "Hogar", origen="hogar")
        except Exception as e:
            messagebox.showerror("Error", "Verifica los datos ingresados.")

    def setup_baby_exp_tab(self):
        tk.Label(self.baby_exp_tab, text="Gastos del Bebé", font=("Comic Sans MS", 16), bg="#F7F7F7").pack(pady=5)
        frame = tk.Frame(self.baby_exp_tab, bg="#F7F7F7")
        frame.pack(pady=5)
        tk.Label(frame, text="Item:", bg="#F7F7F7").grid(row=0, column=0, padx=5, pady=3)
        self.mod_baby_item = tk.Entry(frame)
        self.mod_baby_item.grid(row=0, column=1, padx=5, pady=3)
        tk.Label(frame, text="Costo Unitario (MXN):", bg="#F7F7F7").grid(row=1, column=0, padx=5, pady=3)
        self.mod_baby_cost = tk.Entry(frame)
        self.mod_baby_cost.grid(row=1, column=1, padx=5, pady=3)
        tk.Label(frame, text="Periodicidad:", bg="#F7F7F7").grid(row=2, column=0, padx=5, pady=3)
        self.mod_baby_period = ttk.Combobox(frame, values=["único", "mensual", "anual"])
        self.mod_baby_period.current(0)
        self.mod_baby_period.grid(row=2, column=1, padx=5, pady=3)
        tk.Label(frame, text="Frecuencia:", bg="#F7F7F7").grid(row=3, column=0, padx=5, pady=3)
        self.mod_baby_freq = tk.Entry(frame)
        self.mod_baby_freq.grid(row=3, column=1, padx=5, pady=3)
        btn_calc = ttk.Button(self.baby_exp_tab, text="Calcular Gasto Anual", style="Infantil.TButton", command=self.calc_mod_baby)
        btn_calc.pack(pady=5)
        self.mod_baby_result = tk.Label(self.baby_exp_tab, text="", bg="#F7F7F7", font=("Arial", 12))
        self.mod_baby_result.pack(pady=5)

    def calc_mod_baby(self):
        try:
            item = self.mod_baby_item.get()
            cost = float(self.mod_baby_cost.get())
            period = self.mod_baby_period.get()
            freq = int(self.mod_baby_freq.get())
            expense = BabyExpense(item, cost, period, freq)
            total = expense.total(12)
            self.mod_baby_result.config(text=f"Gasto Anual: {total:.2f} MXN")
            from modules.db_handler import insertar_gasto
            insertar_gasto(item, cost * freq, period, datetime.date.today().strftime("%Y-%m-%d"), "Bebé", origen="bebé")
        except Exception as e:
            messagebox.showerror("Error", "Verifica los datos ingresados.")

    def setup_hosp_tab(self):
        tk.Label(self.hosp_tab, text="Gastos Hospitalarios/Postparto", font=("Comic Sans MS", 16), bg="#F7F7F7").pack(pady=5)
        frame = tk.Frame(self.hosp_tab, bg="#F7F7F7")
        frame.pack(pady=5)
        tk.Label(frame, text="Descripción:", bg="#F7F7F7").grid(row=0, column=0, padx=5, pady=3)
        self.mod_hosp_item = tk.Entry(frame)
        self.mod_hosp_item.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(frame, text="Costo (MXN):", bg="#F7F7F7").grid(row=1, column=0, padx=5, pady=3)
        self.mod_hosp_cost = tk.Entry(frame)
        self.mod_hosp_cost.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(frame, text="Fecha (YYYY-MM-DD):", bg="#F7F7F7").grid(row=2, column=0, padx=5, pady=3)
        self.mod_hosp_date = tk.Entry(frame)
        self.mod_hosp_date.grid(row=2, column=1, padx=5, pady=5)
        btn_reg = ttk.Button(self.hosp_tab, text="Registrar Gasto Hospitalario", style="Infantil.TButton", command=self.reg_mod_hosp)
        btn_reg.pack(pady=5)
        self.mod_hosp_result = tk.Label(self.hosp_tab, text="", bg="#F7F7F7", font=("Arial", 12))
        self.mod_hosp_result.pack(pady=5)

    def reg_mod_hosp(self):
        try:
            item = self.mod_hosp_item.get()
            cost = float(self.mod_hosp_cost.get())
            fecha = self.mod_hosp_date.get()
            datetime.datetime.strptime(fecha, "%Y-%m-%d")
            expense = HospitalExpense(item, cost, fecha)
            self.mod_hosp_result.config(text=f"Gasto '{item}' registrado: {cost:.2f} MXN en {fecha}")
            from modules.db_handler import insertar_gasto
            insertar_gasto(item, cost, "único", fecha, "Hospital", origen="hospital")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {e}")

    def setup_events_tab(self):
        tk.Label(self.events_tab, text="Documentación y Eventos", font=("Comic Sans MS", 16), bg="#F7F7F7").pack(pady=5)
        frame = tk.Frame(self.events_tab, bg="#F7F7F7")
        frame.pack(pady=5)
        tk.Label(frame, text="Evento:", bg="#F7F7F7").grid(row=0, column=0, padx=5, pady=3)
        self.mod_event = tk.Entry(frame)
        self.mod_event.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(frame, text="Costo (MXN):", bg="#F7F7F7").grid(row=1, column=0, padx=5, pady=3)
        self.mod_event_cost = tk.Entry(frame)
        self.mod_event_cost.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(frame, text="Fecha (YYYY-MM-DD):", bg="#F7F7F7").grid(row=2, column=0, padx=5, pady=3)
        self.mod_event_date = tk.Entry(frame)
        self.mod_event_date.grid(row=2, column=1, padx=5, pady=5)
        btn_reg = ttk.Button(self.events_tab, text="Registrar Evento", style="Infantil.TButton", command=self.reg_mod_event)
        btn_reg.pack(pady=5)
        self.mod_event_result = tk.Label(self.events_tab, text="", bg="#F7F7F7", font=("Arial", 12))
        self.mod_event_result.pack(pady=5)

    def reg_mod_event(self):
        try:
            event = self.mod_event.get()
            cost = float(self.mod_event_cost.get())
            date = self.mod_event_date.get()
            datetime.datetime.strptime(date, "%Y-%m-%d")
            event_expense = EventExpense(event, cost, date)
            self.mod_event_result.config(text=f"Evento '{event}' registrado: {cost:.2f} MXN en {date}")
            from modules.db_handler import insertar_gasto
            insertar_gasto(event, cost, "único", date, "Eventos", origen="documentacion")
        except Exception as e:
            messagebox.showerror("Error", "Verifica los datos ingresados.")

    def setup_services_tab(self):
        tk.Label(self.services_tab, text="Servicios y Telefonía", font=("Comic Sans MS", 16), bg="#F7F7F7").pack(pady=5)
        frame = tk.Frame(self.services_tab, bg="#F7F7F7")
        frame.pack(pady=5)
        tk.Label(frame, text="Servicio:", bg="#F7F7F7").grid(row=0, column=0, padx=5, pady=3)
        self.mod_service = tk.Entry(frame)
        self.mod_service.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(frame, text="Costo (MXN):", bg="#F7F7F7").grid(row=1, column=0, padx=5, pady=3)
        self.mod_service_cost = tk.Entry(frame)
        self.mod_service_cost.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(frame, text="Periodicidad:", bg="#F7F7F7").grid(row=2, column=0, padx=5, pady=3)
        self.mod_service_period = ttk.Combobox(frame, values=["único", "mensual", "anual"])
        self.mod_service_period.current(0)
        self.mod_service_period.grid(row=2, column=1, padx=5, pady=5)
        btn_calc = ttk.Button(self.services_tab, text="Calcular Gasto Anual", style="Infantil.TButton", command=self.calc_mod_service)
        btn_calc.pack(pady=5)
        self.mod_service_result = tk.Label(self.services_tab, text="", bg="#F7F7F7", font=("Arial", 12))
        self.mod_service_result.pack(pady=5)

    def calc_mod_service(self):
        try:
            service = self.mod_service.get()
            cost = float(self.mod_service_cost.get())
            period = self.mod_service_period.get()
            expense = ServiceExpense(service, cost, period)
            total = expense.total(12)
            self.mod_service_result.config(text=f"Gasto Anual: {total:.2f} MXN")
            from modules.db_handler import insertar_gasto
            insertar_gasto(service, cost, period, datetime.date.today().strftime("%Y-%m-%d"), "Servicios", origen="servicios")
        except Exception as e:
            messagebox.showerror("Error", "Verifica los datos ingresados.")

    def setup_org_tab(self):
        tk.Label(self.org_tab, text="Organización Familiar Integral", font=("Comic Sans MS", 16), bg="#F7F7F7").pack(pady=5)
        frame = tk.Frame(self.org_tab, bg="#F7F7F7")
        frame.pack(pady=5)
        tk.Label(frame, text="Horas para Dormir:", bg="#F7F7F7").grid(row=0, column=0, padx=5, pady=3)
        self.org_sleep = tk.Entry(frame)
        self.org_sleep.grid(row=0, column=1, padx=5, pady=3)
        tk.Label(frame, text="Horas para Trabajo:", bg="#F7F7F7").grid(row=1, column=0, padx=5, pady=3)
        self.org_work = tk.Entry(frame)
        self.org_work.grid(row=1, column=1, padx=5, pady=3)
        tk.Label(frame, text="Horas para Estudio:", bg="#F7F7F7").grid(row=2, column=0, padx=5, pady=3)
        self.org_study = tk.Entry(frame)
        self.org_study.grid(row=2, column=1, padx=5, pady=3)
        tk.Label(frame, text="Horas para Cuidado del Bebé:", bg="#F7F7F7").grid(row=3, column=0, padx=5, pady=3)
        self.org_care = tk.Entry(frame)
        self.org_care.grid(row=3, column=1, padx=5, pady=3)
        tk.Label(frame, text="Horas para Tareas del Hogar:", bg="#F7F7F7").grid(row=4, column=0, padx=5, pady=3)
        self.org_house = tk.Entry(frame)
        self.org_house.grid(row=4, column=1, padx=5, pady=3)
        btn_plan = ttk.Button(self.org_tab, text="Planificar Horarios", style="Infantil.TButton", command=self.plan_family)
        btn_plan.pack(pady=5)
        self.org_result = tk.Label(self.org_tab, text="", bg="#F7F7F7", font=("Arial", 12), justify="left")
        self.org_result.pack(pady=5)

    def plan_family(self):
        try:
            responsabilidades = {
                "Dormir": float(self.org_sleep.get()),
                "Trabajo": float(self.org_work.get()),
                "Estudio": float(self.org_study.get()),
                "Cuidado del Bebé": float(self.org_care.get()),
                "Tareas del Hogar": float(self.org_house.get())
            }
            reporte = planificar_horarios(responsabilidades)
            self.org_result.config(text=reporte)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def setup_extra_graph_tab(self):
        title = tk.Label(self.extra_graph_tab, text="Gráficas Extras", font=("Comic Sans MS", 20), bg="#F7F7F7")
        title.pack(pady=10)
        btn_volver = ttk.Button(self.extra_graph_tab, text="Volver al Inicio",
                                image=self.controller.icon_back, compound="left",
                                style="Infantil.TButton", command=lambda: self.controller.show_frame(HomePage))
        btn_volver.pack(pady=5)

if __name__ == "__main__":
    app = App()
    app.mainloop()
