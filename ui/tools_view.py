# ui/tools_view.py
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
from tkinter import filedialog as fd, messagebox

from ui.utils import setup_window, ejecutar_en_hilo
from core.pdf_engine import merge_pdfs  # Asumo que esta es tu función del core
from core.config_manager import get_last_dir, set_last_dir
from ui.utils import setup_window, ejecutar_en_hilo, native_open_files, native_save_file

def open_merge_pdfs_window(root):
    root.withdraw() # Ocultar ventana principal
    
    win = tk.Toplevel(root)
    # Cambiamos maximize=False y definimos un tamaño compacto (600x450)
    setup_window(win, "Unir Archivos PDF", 0.5, 0.6, min_w=600, min_h=450, maximize=False)
    
    def on_close():
        root.deiconify()
        win.destroy()
        
    win.protocol("WM_DELETE_WINDOW", on_close)

    # ================= LAYOUT =================
    main_frame = ttk.Frame(win, padding=20)
    main_frame.pack(fill=BOTH, expand=True)
    
    ttk.Label(main_frame, text="Archivos a unir (El orden de arriba hacia abajo será el final):", font=("Arial", 10)).pack(anchor=W, pady=(0, 5))

    # Contenedor central (Lista + Botones laterales)
    center_frame = ttk.Frame(main_frame)
    center_frame.pack(fill=BOTH, expand=True)

    # Lista con Scrollbar
    list_frame = ttk.Frame(center_frame)
    list_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
    
    v_scroll = ttk.Scrollbar(list_frame, orient=VERTICAL)
    listbox = tk.Listbox(list_frame, yscrollcommand=v_scroll.set, bg="#2b2b2b", fg="white", 
                         selectbackground="#375a7f", borderwidth=1, highlightthickness=0, font=("Arial", 10))
    v_scroll.config(command=listbox.yview)
    v_scroll.pack(side=RIGHT, fill=Y)
    listbox.pack(side=LEFT, fill=BOTH, expand=True)

    # Lista de rutas en memoria
    pdf_files = []

    # ================= FUNCIONES DE LOS BOTONES =================
    def add_pdfs():
        files = native_open_files(
            title="Selecciona PDFs para unir",
            initialdir=get_last_dir(),
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if files:
            # Validación estricta
            valid_files = [f for f in files if f.lower().endswith(".pdf")]
            if valid_files: set_last_dir(valid_files[0])
            
            for f in valid_files:
                if f not in pdf_files: 
                    pdf_files.append(f)
                    listbox.insert(tk.END, os.path.basename(f))

    def move_up():
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx > 0:
            # Intercambiar en la interfaz
            text = listbox.get(idx)
            listbox.delete(idx)
            listbox.insert(idx - 1, text)
            # Intercambiar en la lista de memoria
            pdf_files[idx], pdf_files[idx - 1] = pdf_files[idx - 1], pdf_files[idx]
            # Mantener la selección
            listbox.select_set(idx - 1)

    def move_down():
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx < listbox.size() - 1:
            text = listbox.get(idx)
            listbox.delete(idx)
            listbox.insert(idx + 1, text)
            pdf_files[idx], pdf_files[idx + 1] = pdf_files[idx + 1], pdf_files[idx]
            listbox.select_set(idx + 1)

    def remove_selected():
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        listbox.delete(idx)
        pdf_files.pop(idx)
        # Seleccionar el siguiente disponible
        if listbox.size() > 0:
            listbox.select_set(min(idx, listbox.size() - 1))

    def clear_all():
        listbox.delete(0, tk.END)
        pdf_files.clear()

    # ================= BOTONES LATERALES =================
    btn_frame = ttk.Frame(center_frame)
    btn_frame.pack(side=RIGHT, fill=Y)

    ttk.Button(btn_frame, text="➕ Añadir PDFs", bootstyle="primary-outline", command=add_pdfs).pack(fill=X, pady=(0, 10))
    ttk.Button(btn_frame, text="↑ Subir", bootstyle="info-outline", command=move_up).pack(fill=X, pady=2)
    ttk.Button(btn_frame, text="↓ Bajar", bootstyle="info-outline", command=move_down).pack(fill=X, pady=2)
    ttk.Frame(btn_frame, height=2).pack(pady=5) # Separador
    ttk.Button(btn_frame, text="🗑️ Quitar", bootstyle="warning-outline", command=remove_selected).pack(fill=X, pady=2)
    ttk.Button(btn_frame, text="🧹 Limpiar Todo", bootstyle="danger-outline", command=clear_all).pack(fill=X, pady=2)

    # ================= ACCIÓN FINAL (CON HILOS) =================
    def save_merged():
        if len(pdf_files) < 2:
            messagebox.showwarning("Atención", "Necesitas al menos 2 PDFs para unirlos.")
            return
            
        out_path = native_save_file(
            title="Guardar PDF unido",
            initialdir=get_last_dir(),
            defaultextension=".pdf"
        )
        if not out_path: return
        set_last_dir(out_path)

        def tarea_unir():
            merge_pdfs(pdf_files, out_path)
            return out_path
            
        def exito(res):
            messagebox.showinfo("Éxito", "PDFs unidos correctamente.")
            on_close()
            
        def error(e):
            messagebox.showerror("Error", f"Fallo al unir:\n{e}")

        # Usamos nuestro nuevo sistema de hilos para que no se congele si unen muchos archivos
        ejecutar_en_hilo(win, tarea_unir, "Uniendo documentos...", exito, error)

    # Botón grande abajo
    ttk.Button(main_frame, text="UNIR Y GUARDAR PDF", bootstyle="success", padding=15, command=save_merged).pack(fill=X, pady=(20, 0))