# ui/editor_view.py
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import pdf2image
from tkinter import filedialog as fd, messagebox, simpledialog
from PIL import ImageTk
from pypdf import PdfReader
from ui.utils import setup_window, ejecutar_en_hilo
from core.pdf_engine import save_edited_pdf
from core.config_manager import get_last_dir, set_last_dir
from ui.utils import setup_window, ejecutar_en_hilo, native_open_file, native_save_file 

def edit_pdf_window(root, preloaded_path=None):
    if preloaded_path:
        pdf_path = preloaded_path
    else:
        pdf_path = native_open_file(
            title="Selecciona el PDF a editar",
            initialdir=get_last_dir(), 
            filetypes=[("PDF", "*.pdf")]
        )
    
    if not pdf_path.lower().endswith(".pdf"):
        messagebox.showerror("Archivo no válido", "Por favor, selecciona un documento PDF válido.")
        return
        
    set_last_dir(pdf_path)

    root.withdraw() 

    reader = PdfReader(pdf_path)
    pdf_password = None

    if reader.is_encrypted:
        pdf_password = simpledialog.askstring("PDF Protegido", "Este archivo está encriptado.\nIngresa la contraseña:", show='*')
        if not pdf_password:
            root.deiconify() 
            return
            
        try:
            resultado = reader.decrypt(pdf_password)
            if resultado == 0:
                messagebox.showerror("Error", "Contraseña incorrecta.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al desencriptar el archivo:\n{e}")
            return

    win = tk.Toplevel(root)
    setup_window(win, f"Editando: {os.path.basename(pdf_path)}", 0.9, 0.9, maximize=True)
    
    def on_close():
        root.deiconify() 
        win.destroy()    

    win.protocol("WM_DELETE_WINDOW", on_close)

    pages_data = list(range(len(reader.pages)))
    rotations = {i: 0 for i in pages_data}
    current = {"idx": 0}

    # ================= LAYOUT MODERNO (TTKBOOTSTRAP) =================
    right_frame = ttk.Frame(win, width=220, padding=10)
    right_frame.pack(side=RIGHT, fill=Y)
    right_frame.pack_propagate(False)

    left_frame = ttk.Frame(win)
    left_frame.pack(side=LEFT, fill=BOTH, expand=True)

    # El Canvas se queda en tk porque ttkbootstrap no tiene un Canvas nativo, 
    # pero le ponemos un fondo oscuro acorde al tema Darkly
    canvas = tk.Canvas(left_frame, bg="#222222", highlightthickness=0)
    v_scroll = ttk.Scrollbar(left_frame, orient=VERTICAL, command=canvas.yview)
    h_scroll = ttk.Scrollbar(left_frame, orient=HORIZONTAL, command=canvas.xview)
    canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    h_scroll.pack(side=BOTTOM, fill=X)
    v_scroll.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)

    # Frame interno para la imagen
    inner_frame = tk.Frame(canvas, bg="#222222")
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")
    page_lbl = tk.Label(inner_frame, bg="#222222")
    page_lbl.pack(padx=20, pady=20)

    def update_region(e=None): canvas.configure(scrollregion=canvas.bbox("all"))
    inner_frame.bind("<Configure>", update_region)

    # === NUEVO: SCROLL CON RUEDA DEL RATÓN ===
    def _on_mousewheel(event):
        # Detectar evento en Linux (event.num) o Windows/Mac (event.delta)
        if (hasattr(event, 'num') and event.num == 4) or (hasattr(event, 'delta') and event.delta > 0):
            canvas.yview_scroll(-1, "units") # Desplazar arriba
        elif (hasattr(event, 'num') and event.num == 5) or (hasattr(event, 'delta') and event.delta < 0):
            canvas.yview_scroll(1, "units")  # Desplazar abajo

    # Enlazar los eventos a la ventana actual para compatibilidad total
    win.bind("<MouseWheel>", _on_mousewheel)
    win.bind("<Button-4>", _on_mousewheel)
    win.bind("<Button-5>", _on_mousewheel)
    
    

    # Renderizado con pdf2image
    try:
        if pdf_password:
            images = pdf2image.convert_from_path(pdf_path, dpi=100, userpw=pdf_password)
        else:
            images = pdf2image.convert_from_path(pdf_path, dpi=100)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo renderizar el PDF:\n{e}")
        win.destroy()
        return

    # Etiqueta de información moderna
    lbl_info = ttk.Label(right_frame, text="", font=("Arial", 11, "bold"), justify=CENTER)
    lbl_info.pack(pady=(10, 20))

    # ================= FUNCIONES DEL EDITOR =================
    def show_page(i):
        if not pages_data:
            page_lbl.config(image="")
            lbl_info.config(text="Documento Vacío")
            return
        
        i = max(0, min(i, len(pages_data)-1))
        current["idx"] = i
        real_idx = pages_data[i] 
        
        angle = rotations.get(real_idx, 0)
        img = images[real_idx].rotate(angle, expand=True)
        
        if img.width > 1500: 
            img = img.resize((1500, int(1500*img.height/img.width)))
            
        tk_img = ImageTk.PhotoImage(img)
        page_lbl.config(image=tk_img)
        page_lbl.image = tk_img
        
        lbl_info.config(text=f"Posición: {i+1} / {len(pages_data)}\n(Pág. Original: {real_idx+1})")
        update_region()
    
    # ================= CREACIÓN DE BOTONES MODERNOS =================
    ttk.Button(right_frame, text="<< Anterior", bootstyle="primary-outline", command=lambda: show_page(current["idx"]-1)).pack(fill=X, pady=3)
    ttk.Button(right_frame, text="Siguiente >>", bootstyle="primary-outline", command=lambda: show_page(current["idx"]+1)).pack(fill=X, pady=3)
    
    ttk.Separator(right_frame, orient=HORIZONTAL).pack(fill=X, pady=15)
    
    ttk.Button(right_frame, text="Rotar Derecha ⟳", bootstyle="info-outline", command=lambda: rotate(90)).pack(fill=X, pady=3)
    ttk.Button(right_frame, text="Rotar Izquierda ⟲", bootstyle="info-outline", command=lambda: rotate(-90)).pack(fill=X, pady=3)
    
    ttk.Separator(right_frame, orient=HORIZONTAL).pack(fill=X, pady=15)
    
    ttk.Button(right_frame, text="Mover Atrás ◀", bootstyle="secondary-outline", command=lambda: move_p(-1)).pack(fill=X, pady=3)
    ttk.Button(right_frame, text="Mover Adelante ▶", bootstyle="secondary-outline", command=lambda: move_p(1)).pack(fill=X, pady=3)
    
    ttk.Separator(right_frame, orient=HORIZONTAL).pack(fill=X, pady=15)
    
    ttk.Button(right_frame, text="Eliminar Página", bootstyle="danger", command=lambda: delete_p()).pack(fill=X, pady=3)
    # =====================================================================

    def rotate(deg):
        idx = pages_data[current["idx"]]
        rotations[idx] = (rotations[idx] + deg) % 360
        show_page(current["idx"])

    def delete_p():
        if pages_data:
            idx = current["idx"]
            pages_data.pop(idx)
            show_page(idx if idx < len(pages_data) else idx-1)
    
    def move_p(direction):
        if not pages_data: return
        idx = current["idx"]
        new_idx = idx + direction
        if 0 <= new_idx < len(pages_data):
            pages_data[idx], pages_data[new_idx] = pages_data[new_idx], pages_data[idx]
            show_page(new_idx)   

    def save_changes():
        path = native_save_file(
            title="Guardar PDF editado",
            initialdir=get_last_dir(),
            defaultextension=".pdf"
        )
        if not path: return
        set_last_dir(path)

        def tarea_guardar():
            save_edited_pdf(pdf_path, path, pages_data, rotations, pdf_password)
            return path
            
        def exito(resultado):
            messagebox.showinfo("Hecho", "Guardado exitosamente.")
            on_close() 
            
        def error(e):
            messagebox.showerror("Error", f"Ocurrió un error al guardar:\n{e}")

        ejecutar_en_hilo(win, tarea_guardar, "Guardando y reestructurando PDF...", exito, error)
        
    # Botón de guardado final anclado abajo
    ttk.Button(right_frame, text="GUARDAR PDF", bootstyle="success", padding=15, command=save_changes).pack(side=BOTTOM, fill=X, pady=10)
    
    show_page(0)