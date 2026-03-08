#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
from PIL import Image, ImageTk, ImageEnhance

# Importaciones de tu arquitectura MVC
from ui.utils import setup_window
from ui.tools_view import open_merge_pdfs_window
from ui.scanner_view import open_scanner_window
from ui.editor_view import edit_pdf_window
from ui.signer_view import open_sign_pdf_window
from controllers.pdf_ctrl import handle_docx_to_pdf
import sys
import traceback
from core.logger import app_logger

# ================= RUTAS DE RECURSOS =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BTN_DIR = os.path.join(ASSETS_DIR, "buttons")
ICONS_DIR = os.path.join(ASSETS_DIR, "assets")

def crear_tarjeta(parent, filename, comando, fila, columna, colspan=1):
    """Crea un botón de imagen con un efecto de iluminación al pasar el ratón."""
    img_path = os.path.join(BTN_DIR, filename)
    
    try:
        pil_img = Image.open(img_path)
        pil_img = pil_img.resize((282, 153), Image.Resampling.LANCZOS)
        
        # 1. Imagen en estado normal
        tk_img_normal = ImageTk.PhotoImage(pil_img)
        
        # 2. Imagen en estado "Hover" (Iluminada un 15%)
        enhancer = ImageEnhance.Brightness(pil_img)
        pil_img_hover = enhancer.enhance(1.15) # 1.15 significa 15% más de brillo
        tk_img_hover = ImageTk.PhotoImage(pil_img_hover)
        
    except Exception as e:
        print(f"Error cargando imagen {filename}: {e}")
        tk_img_normal = tk.PhotoImage() 
        tk_img_hover = tk.PhotoImage() 

    style = ttk.Style()
    bg_color = style.colors.bg

    lbl_btn = tk.Label(
        parent,
        image=tk_img_normal,
        bg=bg_color,                
        borderwidth=0,              
        highlightthickness=0,       
        cursor="hand2"              
    )
    
    # Guardamos ambas referencias para el recolector de basura
    lbl_btn.image_normal = tk_img_normal 
    lbl_btn.image_hover = tk_img_hover
    
    # ================= EVENTOS DE INTERACCIÓN =================
    # Clic
    lbl_btn.bind("<Button-1>", lambda event: comando())
    
    # El cursor entra (Iluminar)
    lbl_btn.bind("<Enter>", lambda event: lbl_btn.config(image=lbl_btn.image_hover))
    
    # El cursor sale (Volver a la normalidad)
    lbl_btn.bind("<Leave>", lambda event: lbl_btn.config(image=lbl_btn.image_normal))
    
    lbl_btn.grid(row=fila, column=columna, columnspan=colspan, padx=8, pady=8)
    return lbl_btn
def main():
    root = ttk.Window(themename="darkly")
    # Ajustamos un poco el tamaño de la ventana para que abrace mejor las imágenes
    setup_window(root, "Universal PDF Suite", 0.6, 0.6, 640, 700)
    
    # ================= RED DE SEGURIDAD (LOGGING GLOBAL) =================
    def manejar_excepcion_global(exc_type, exc_value, exc_traceback):
        """Captura errores fatales en el hilo principal de Python."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        app_logger.critical("Excepción no controlada", exc_info=(exc_type, exc_value, exc_traceback))

    def manejar_excepcion_tkinter(exc_type, exc_value, exc_traceback):
        """Captura errores silenciosos que ocurren al hacer clic en botones (Tkinter callbacks)."""
        app_logger.error("Excepción en Tkinter", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Sobrescribimos el comportamiento por defecto de Python y Tkinter
    sys.excepthook = manejar_excepcion_global
    root.report_callback_exception = manejar_excepcion_tkinter

    app_logger.info("Iniciando Universal PDF Suite...")

    # Redujimos el padding general del contenedor principal
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(expand=True, fill=BOTH)

    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)

# ================= CABECERA: LOGO + TÍTULO =================
    header_frame = ttk.Frame(main_frame)
    header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20))

    # 1. Cargar y mostrar el logo encima
    logo_path = os.path.join(ASSETS_DIR, "icon.png")
    try:
        if os.path.exists(logo_path):
            logo_pil = Image.open(logo_path).resize((80, 80), Image.Resampling.LANCZOS)
            logo_tk = ImageTk.PhotoImage(logo_pil)
            
            # Usamos tk.Label para evitar bordes nativos, igual que en los botones
            style = ttk.Style()
            lbl_logo = tk.Label(header_frame, image=logo_tk, bg=style.colors.bg, borderwidth=0)
            lbl_logo.image = logo_tk 
            lbl_logo.pack(pady=(0, 10)) # Separación entre el logo y el texto
    except Exception as e:
        print(f"Error cargando el logo principal: {e}")

    # 2. El título reaparece justo debajo
    lbl_title = ttk.Label(header_frame, text="Universal PDF Suite", font=("Arial", 24, "bold"))
    lbl_title.pack()

    logo_path = os.path.join(ASSETS_DIR, "icon.png")

    # Eliminamos el texto "Universal PDF Suite" ya que el logo grande lo representa bien,
    # pero puedes descomentar las siguientes líneas si prefieres mantenerlo:
    # lbl_title = ttk.Label(header_frame, text="Universal PDF Suite", font=("Arial", 24, "bold"))
    # lbl_title.pack(pady=(5,0))

    # ================= GRID DE TARJETAS DE IMAGEN =================
    crear_tarjeta(main_frame, "btn_edit.png", 
                  lambda: edit_pdf_window(root), 
                  fila=1, columna=0)
                  
    crear_tarjeta(main_frame, "btn_scan.png", 
                  lambda: open_scanner_window(root, lambda p: edit_pdf_window(root, p)), 
                  fila=1, columna=1)

    crear_tarjeta(main_frame, "btn_sign.png", 
                  lambda: open_sign_pdf_window(root), 
                  fila=2, columna=0)
                  
    crear_tarjeta(main_frame, "btn_merge.png", 
                  lambda: open_merge_pdfs_window(root), 
                  fila=2, columna=1)

    crear_tarjeta(main_frame, "btn_docx.png", 
                  handle_docx_to_pdf, 
                  fila=3, columna=0, colspan=2)

    # ================= LIMPIEZA Y CIERRE =================
    def safe_exit():
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", safe_exit)
    root.mainloop()

if __name__ == "__main__":
    main()