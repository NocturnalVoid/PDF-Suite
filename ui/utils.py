# ui/utils.py
import platform
import subprocess
import tkinter as tk
from tkinter import filedialog as fd
import ttkbootstrap as ttk
import platform
import os
import threading  # <--- NUEVO IMPORTs



def setup_window(window, title, width_percent=0.8, height_percent=0.8, min_w=900, min_h=650, maximize=False):
    """Configura el tamaño, posición centrada, título e icono de una ventana."""
    window.title(title)
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    w = int(screen_width * width_percent)
    h = int(screen_height * height_percent)
    w = max(w, min_w)
    h = max(h, min_h)
    
    x = (screen_width - w) // 2
    y = (screen_height - h) // 2
    window.geometry(f"{w}x{h}+{x}+{y}")
    window.minsize(min_w, min_h)
    
    # === LÓGICA DE ICONO CROSS-PLATFORM ===
    # Detectamos la ruta absoluta de la carpeta "gestor_pdf"
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(base_dir, "assets")
    icons_dir = os.path.join(assets_dir, "icons")
    
    try:
        if platform.system() == "Windows":
            icon_path = os.path.join(assets_dir, "icon.ico")
            if os.path.exists(icon_path):
                window.iconbitmap(icon_path)
        else: # Linux (Debian/X11)
            icon_path = os.path.join(assets_dir, "icon.png")
            if os.path.exists(icon_path):
                icon_img = tk.PhotoImage(file=icon_path)
                # Forzamos a Tkinter a usar este icono en lugar del de ttkbootstrap
                window.iconphoto(True, icon_img)
    except Exception as e:
        print(f"Aviso: No se pudo forzar el icono del sistema ({e})")
    # === LÓGICA DE MAXIMIZADO ===
    if maximize:
        try:
            window.state('zoomed') 
        except tk.TclError:
            try:
                window.attributes('-zoomed', True) 
            except Exception:
                pass
            
# ================= NUEVO SISTEMA DE HILOS Y CARGA =================
def ejecutar_en_hilo(parent, tarea_func, msg_carga="Procesando...", on_success=None, on_error=None):
    """
    Ejecuta una tarea pesada en un hilo secundario mostrando una barra de progreso.
    Bloquea la ventana padre hasta que termine.
    """
    # 1. Crear ventana emergente (Modal)
    loading_win = tk.Toplevel(parent)
    loading_win.title("Por favor espera")
    
    # Centrar la ventanita
    w, h = 300, 100
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
    loading_win.geometry(f"{w}x{h}+{x}+{y}")
    
    loading_win.transient(parent) # Mantenerla siempre encima del padre
    loading_win.grab_set()        # Bloquear clics en el resto de la aplicación
    loading_win.resizable(False, False)
    
    # 2. Diseño de la ventana de carga
    lbl = ttk.Label(loading_win, text=msg_carga, font=("Arial", 11))
    lbl.pack(pady=(15, 10))
    
    progress = ttk.Progressbar(loading_win, mode='indeterminate', bootstyle="info")
    progress.pack(fill=tk.X, padx=20)
    progress.start(10) # Iniciar animación fluida
    
    resultado = []
    error = []

    # 3. La función que correrá en el fondo
    def worker():
        try:
            res = tarea_func() # Ejecutamos el trabajo pesado
            resultado.append(res)
        except Exception as e:
            error.append(e)

    # Iniciar el hilo
    hilo = threading.Thread(target=worker, daemon=True)
    hilo.start()

    # 4. Monitor para revisar cuándo termina el hilo sin bloquear Tkinter
    def revisar_hilo():
        if hilo.is_alive():
            parent.after(100, revisar_hilo) # Revisar de nuevo en 100ms
        else:
            progress.stop()
            loading_win.destroy() # Cerrar ventanita
            
            # Devolver resultados al hilo principal
            if error:
                if on_error: on_error(error[0])
            else:
                if on_success: on_success(resultado[0] if resultado else None)

    # Iniciar el monitor
    revisar_hilo()
    
# ================= DIÁLOGOS DE ARCHIVO NATIVOS =================
def native_open_file(title="Abrir Archivo", initialdir=None, filetypes=None):
    """Fuerza el explorador nativo en Linux usando zenity con filtros. En Windows usa el estándar."""
    if platform.system() == "Linux":
        try:
            cmd = ["zenity", "--file-selection", f"--title={title}"]
            if initialdir: cmd.append(f"--filename={initialdir}/")
            
            # === NUEVO: Traducción de filtros a formato Zenity ===
            if filetypes:
                for desc, ext in filetypes:
                    # Convierte ("PDF", "*.pdf") a "--file-filter=PDF | *.pdf"
                    cmd.append(f"--file-filter={desc} | {ext}")
                    
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0: return res.stdout.strip()
            return ""
        except FileNotFoundError: pass 
    
    # Fallback si no hay zenity o si estamos en Windows
    if not filetypes: filetypes = [("Archivos", "*.*")]
    return fd.askopenfilename(title=title, initialdir=initialdir, filetypes=filetypes)

def native_save_file(title="Guardar como", initialdir=None, defaultextension=".pdf"):
    if platform.system() == "Linux":
        try:
            cmd = ["zenity", "--file-selection", "--save", "--confirm-overwrite", f"--title={title}"]
            if initialdir: cmd.append(f"--filename={initialdir}/")
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                path = res.stdout.strip()
                if not path.endswith(defaultextension): path += defaultextension
                return path
            return ""
        except FileNotFoundError: pass
    
    return fd.asksaveasfilename(title=title, initialdir=initialdir, defaultextension=defaultextension)

def native_open_files(title="Abrir múltiples archivos", initialdir=None, filetypes=None):
    if platform.system() == "Linux":
        try:
            cmd = ["zenity", "--file-selection", "--multiple", "--separator=|", f"--title={title}"]
            if initialdir: cmd.append(f"--filename={initialdir}/")
            
            if filetypes:
                for desc, ext in filetypes:
                    # zenity requiere los formatos múltiples separados por espacio
                    ext_zenity = ext.replace(";", " ") 
                    cmd.append(f"--file-filter={desc} | {ext_zenity}")
                    
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0: return res.stdout.strip().split("|")
            return []
        except FileNotFoundError: pass
    
    if not filetypes: filetypes = [("Archivos", "*.*")]
    # Convertimos la tupla de Tkinter a lista para mantener consistencia
    return list(fd.askopenfilenames(title=title, initialdir=initialdir, filetypes=filetypes))


