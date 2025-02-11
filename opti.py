import os
import shutil
import subprocess
import psutil
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox, Menu, ttk as tkttk
import threading
import platform
import speedtest
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import schedule
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fpdf import FPDF

# Crear archivo de logs
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"optimizacion_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

def escribir_log(mensaje, log_widget=None):
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {mensaje}\n")
    print(mensaje)
    if log_widget:
        log_widget.insert(tk.END, mensaje + "\n")
        log_widget.see(tk.END)

# Funciones de optimización
def limpiar_temporales(log_widget, barra):
    rutas = [
        os.getenv('TEMP'),
        os.path.join(os.getenv('SystemRoot'), 'Prefetch'),
        os.path.join(os.getenv('SystemRoot'), 'SoftwareDistribution', 'Download')
    ]
    progreso = 0
    for ruta in rutas:
        if os.path.exists(ruta):
            escribir_log(f"Limpiando: {ruta}", log_widget)
            try:
                for archivo in os.listdir(ruta):
                    archivo_path = os.path.join(ruta, archivo)
                    if os.path.isfile(archivo_path) or os.path.islink(archivo_path):
                        os.remove(archivo_path)
                    elif os.path.isdir(archivo_path):
                        shutil.rmtree(archivo_path)
                escribir_log(f"{ruta} limpiada correctamente.", log_widget)
            except Exception as e:
                escribir_log(f"Error al limpiar {ruta}: {e}", log_widget)
        progreso += 33
        barra['value'] = progreso
        log_widget.update()
    barra['value'] = 100

# Limpiador de registro habitual (temp)

def limpiar_registro(log_widget):
    escribir_log("Iniciando limpieza del registro...", log_widget)
    try:
        subprocess.run('powershell.exe Remove-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RunMRU" -Force', shell=True, check=True)
        escribir_log("Limpieza del registro completada.", log_widget)
    except subprocess.CalledProcessError as e:
        escribir_log(f"Error al limpiar el registro: {e}", log_widget)

def ajustes_avanzados_red(log_widget):
    escribir_log("Aplicando ajustes avanzados de red...", log_widget)
    try:
        subprocess.run('netsh int ip reset', shell=True, check=True)
        subprocess.run('netsh winsock reset', shell=True, check=True)
        escribir_log("Ajustes avanzados de red completados.", log_widget)
    except subprocess.CalledProcessError as e:
        escribir_log(f"Error al aplicar ajustes de red: {e}", log_widget)

def desfragmentar_disco(log_widget, barra):
    escribir_log("Iniciando desfragmentación del disco...", log_widget)
    try:
        subprocess.run('defrag C: /U /V', shell=True, check=True)
        escribir_log("Desfragmentación completada.", log_widget)
    except subprocess.CalledProcessError as e:
        escribir_log(f"Error al desfragmentar el disco: {e}", log_widget)
    barra['value'] = 100

def mostrar_notificacion(mensaje):
    messagebox.showinfo("Notificación", mensaje)

# Pantalla de resumen con estadísticas
def mostrar_resumen(log_widget):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disco = psutil.disk_usage('C:').percent
    resumen = f"Resumen de Optimización:\n\nCPU: {cpu}%\nRAM: {ram}%\nDisco: {disco}%\n\n" + open(LOG_FILE).read()
    messagebox.showinfo("Resumen de Optimización", resumen)

# Generación de reporte en PDF
def generar_reporte_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Reporte de Optimización del Sistema", ln=True, align='C')
    pdf.ln(10)
    with open(LOG_FILE, "r") as log:
        for linea in log:
            pdf.multi_cell(0, 10, txt=linea)
    reporte_file = os.path.join(LOG_DIR, "reporte_optimizacion.pdf")
    pdf.output(reporte_file)
    messagebox.showinfo("Reporte Generado", f"Reporte guardado en: {reporte_file}")

# Monitorización de recursos en tiempo real
def monitorizar_recursos(canvas, ax):
    ax.clear()
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disco = psutil.disk_usage('C:').percent
    ax.bar(['CPU', 'RAM', 'Disco'], [cpu, ram, disco], color=['#ff9999', '#66b3ff', '#99ff99'])
    ax.set_ylim(0, 100)
    ax.set_ylabel('Porcentaje de Uso (%)')
    ax.set_title('Monitorización de Recursos en Tiempo Real')
    canvas.draw()
    canvas.get_tk_widget().after(1000, monitorizar_recursos, canvas, ax)

# Interfaz gráfica mejorada con ttkbootstrap y gráficos en tiempo real
def crear_interfaz():
    ventana = ttk.Window(title="Optimización del Sistema", themename="darkly", size=(1500, 700))
    ventana.resizable(False, False)
    
    ttk.Label(ventana, text="Optimización del Sistema", font=("Arial", 16, "bold"), anchor=CENTER).pack(pady=10)
    log_widget = scrolledtext.ScrolledText(ventana, width=110, height=15, state='normal')
    log_widget.pack(padx=10, pady=10)
    
    barra = ttk.Progressbar(ventana, mode='determinate', bootstyle=SUCCESS)
    barra.pack(fill=tk.X, padx=10, pady=10)
    
    frame_botones = ttk.Frame(ventana)
    frame_botones.pack(pady=10)
    
    botones = [
        ("Limpiar Temporales", lambda: threading.Thread(target=limpiar_temporales, args=(log_widget, barra)).start()),
        ("Limpiar Registro", lambda: threading.Thread(target=limpiar_registro, args=(log_widget,)).start()),
        ("Ajustes de Red", lambda: threading.Thread(target=ajustes_avanzados_red, args=(log_widget,)).start()),
        ("Desfragmentar Disco", lambda: threading.Thread(target=desfragmentar_disco, args=(log_widget, barra)).start()),
        ("Mostrar Resumen", lambda: mostrar_resumen(log_widget)),
        ("Generar Reporte PDF", generar_reporte_pdf),
        ("Ejecutar Todo", lambda: threading.Thread(target=ejecutar_todo, args=(log_widget, barra)).start())
    ]
    
    for texto, comando in botones:
        ttk.Button(frame_botones, text=texto, width=25, command=comando, bootstyle=PRIMARY).pack(side=tk.LEFT, padx=5, pady=5)
    
    # Gráfico para monitorización de recursos
    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, ventana)
    canvas.get_tk_widget().pack(padx=10, pady=20)
    monitorizar_recursos(canvas, ax)
    
    ventana.mainloop()

if __name__ == "__main__":
    crear_interfaz()



