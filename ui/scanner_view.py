import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import cv2
import numpy as np
from tkinter import filedialog as fd, messagebox
from PIL import Image, ImageTk, ImageOps

from ui.utils import setup_window
from core.image_processing import detect_and_unwarp_document
from core.config_manager import get_setting, set_setting
from core.config_manager import get_last_dir, set_last_dir
from ui.utils import setup_window, ejecutar_en_hilo, native_open_files, native_save_file

def open_scanner_window(root, on_pdf_created_callback=None):
    root.withdraw() # Ocultar la principal al abrir
    image_list = []
    cv2_cache = {}        
    manual_crops = {}     
    
    current_anim_job = None
    last_selected_idx = -1
    crop_start_xy = None
    
    win = tk.Toplevel(root)
    setup_window(win, "Escanear a PDF Pro", 0.9, 0.85, maximize=True)
    
    def on_close_window():
        nonlocal current_anim_job
        if current_anim_job:
            try: win.after_cancel(current_anim_job)
            except: pass
        root.deiconify() # Restaurar la principal
        win.destroy()
        
    win.protocol("WM_DELETE_WINDOW", on_close_window)

    # ================= LAYOUT PRINCIPAL =================
    # Panel Izquierdo (Sidebar)
    sidebar = ttk.Frame(win, width=350, padding=15)
    sidebar.pack(side=LEFT, fill=Y)
    sidebar.pack_propagate(False) # Evita que el panel se encoja
    
    # Área de visualización (Derecha)
    canvas_frame = ttk.Frame(win, padding=10)
    canvas_frame.pack(side=RIGHT, fill=BOTH, expand=True)

    # ================= SIDEBAR: 1. DOCUMENTOS =================
    frame_docs = ttk.Labelframe(sidebar, text=" 📸 1. Documentos ", padding=10)
    frame_docs.pack(fill=X, pady=(0, 15))

    list_container = ttk.Frame(frame_docs)
    list_container.pack(fill=BOTH, expand=True, pady=(0, 10))
    
    v_scroll = ttk.Scrollbar(list_container, orient=VERTICAL)
    listbox = tk.Listbox(list_container, yscrollcommand=v_scroll.set, bg="#2b2b2b", fg="white", 
                         selectbackground="#375a7f", borderwidth=0, highlightthickness=0)
    v_scroll.config(command=listbox.yview)
    v_scroll.pack(side=RIGHT, fill=Y)
    listbox.pack(side=LEFT, fill=BOTH, expand=True)

    def add_files():
        # Usamos initialdir para que abra la última carpeta usada
        files = native_open_files(
            title="Seleccionar imágenes",
            initialdir=get_last_dir(),
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp")]
        )
        if files:
            # Validación estricta para imágenes
            valid_exts = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
            valid_files = [f for f in files if f.lower().endswith(valid_exts)]
            
            if valid_files: set_last_dir(valid_files[0])
            for f in valid_files:
                if f not in image_list:
                    image_list.append(f)
                    listbox.insert(tk.END, os.path.basename(f))
            if valid_files:
                listbox.select_set(listbox.size() - 1)
                update_preview(True)

    def clear_all_data():
        nonlocal current_anim_job
        if current_anim_job: 
            try: preview_canvas.after_cancel(current_anim_job)
            except: pass
        current_anim_job = None
        image_list.clear()
        cv2_cache.clear()
        manual_crops.clear()
        listbox.delete(0, tk.END)
        preview_canvas.delete("all")

    # Botones de documentos
    btn_box_docs = ttk.Frame(frame_docs)
    btn_box_docs.pack(fill=X)
    ttk.Button(btn_box_docs, text="Añadir Fotos", bootstyle="primary-outline", command=add_files).pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
    ttk.Button(btn_box_docs, text="Limpiar", bootstyle="danger-outline", command=clear_all_data).pack(side=RIGHT, fill=X, expand=True, padx=(5, 0))

# ================= SIDEBAR: 2. AJUSTES =================
    frame_settings = ttk.Labelframe(sidebar, text=" ⚙️ 2. Ajustes de Escaneo ", padding=10)
    frame_settings.pack(fill=X, pady=(0, 15))

    # Leer los valores guardados (o usar los valores por defecto si es la primera vez)
    saved_crop = get_setting("scanner_auto_crop", True)
    saved_mode = get_setting("scanner_mode", "bw")
    saved_thresh = get_setting("scanner_thresh", 15)

    auto_crop_var = tk.BooleanVar(value=saved_crop)
    mode_var = tk.StringVar(value=saved_mode)
    thresh_val = tk.IntVar(value=saved_thresh)

    def on_setting_change(*args): 
        # Guardar automáticamente cuando el usuario cambia algo
        set_setting("scanner_auto_crop", auto_crop_var.get())
        set_setting("scanner_mode", mode_var.get())
        set_setting("scanner_thresh", thresh_val.get())
        update_preview(False)

    # Toggle moderno para el auto-recorte
    ck_crop = ttk.Checkbutton(frame_settings, text="Auto-Recorte Inteligente", variable=auto_crop_var, 
                              bootstyle="success-round-toggle", command=on_setting_change)
    ck_crop.pack(fill=X, pady=(0, 10))

    # Botones de radio para el color
    mode_frame = ttk.Frame(frame_settings)
    mode_frame.pack(fill=X, pady=(0, 10))
    ttk.Radiobutton(mode_frame, text="B/N (Texto)", variable=mode_var, value="bw", command=on_setting_change).pack(side=LEFT, padx=(0, 10))
    ttk.Radiobutton(mode_frame, text="Grises (Foto)", variable=mode_var, value="grayscale", command=on_setting_change).pack(side=LEFT)
    ttk.Radiobutton(mode_frame, text="Original", variable=mode_var, value="original", command=on_setting_change).pack(side=LEFT)

    ttk.Label(frame_settings, text="Nivel de Limpieza (Umbral):").pack(anchor=W)
    thresh_scale = ttk.Scale(frame_settings, from_=3, to=45, orient=HORIZONTAL, variable=thresh_val, bootstyle="info")
    thresh_scale.pack(fill=X, pady=(5, 0))

    # ================= SIDEBAR: 3. RECORTE MANUAL =================
    frame_manual = ttk.Labelframe(sidebar, text=" ✂️ 3. Recorte Manual ", padding=10)
    frame_manual.pack(fill=X, pady=(0, 15))
    
    ttk.Label(frame_manual, text="Dibuja un rectángulo en la imagen\npara forzar un recorte.", 
              font=("Arial", 8), foreground="gray").pack(anchor=W, pady=(0, 5))

    def reset_manual_crop():
        if not listbox.curselection(): return
        idx = listbox.curselection()[0]
        path = image_list[idx]
        if path in manual_crops:
            del manual_crops[path]
            update_preview(False)

    btn_reset_crop = ttk.Button(frame_manual, text="Quitar Recorte Manual", bootstyle="warning-outline", state=DISABLED, command=reset_manual_crop)
    btn_reset_crop.pack(fill=X)

    # ================= SIDEBAR: ACCIÓN FINAL =================
    def save_pdf():
        if not image_list: return
        # También aplicamos la memoria aquí
        path = native_save_file(
            title="Guardar Escaneo como PDF",
            initialdir=get_last_dir(),
            defaultextension=".pdf"
        )
        if not path: return
        set_last_dir(path)
        
        try: 
            if win.winfo_exists(): win.config(cursor="watch")
        except: pass
            
        try:
            pil_imgs = []
            m_thresh = thresh_val.get()
            cur_mode = mode_var.get()
            cur_crop = auto_crop_var.get()
            
            for f in image_list:
                img = get_processed_image(f, cur_mode, cur_crop, m_thresh)
                if img: pil_imgs.append(img)
            
            if pil_imgs:
                pil_imgs[0].save(path, save_all=True, append_images=pil_imgs[1:])
                if win.winfo_exists(): win.config(cursor="")
        
            resp = messagebox.askyesno("Éxito", f"PDF generado en:\n{path}\n\n¿Deseas editar este PDF ahora?")
            on_close_window() # Reemplaza win.destroy() con nuestra función
        
            if resp and on_pdf_created_callback:
                on_pdf_created_callback(path)

        except Exception as e:
            messagebox.showerror("Error", str(e))
            try: 
                if win.winfo_exists(): win.config(cursor="")
            except: pass

    ttk.Button(sidebar, text="GUARDAR PDF", bootstyle="success", padding=15, command=save_pdf).pack(side=BOTTOM, fill=X)

    # ================= ÁREA DE CANVAS (DERECHA) =================
    ttk.Label(canvas_frame, text="Vista Previa", font=("Arial", 12, "bold")).pack(anchor=W, pady=(0, 5))
    preview_canvas = tk.Canvas(canvas_frame, bg="#1a1a1a", highlightthickness=1, highlightbackground="#333", cursor="crosshair")
    preview_canvas.pack(fill=BOTH, expand=True)

    # --- LÓGICA DE PROCESAMIENTO MATRICIAL (Intacta) ---
    def get_base_image(path):
        try:
            pil_orig = Image.open(path)
            pil_orig = ImageOps.exif_transpose(pil_orig) 
            return pil_orig.convert("RGB")
        except: return None
        
    def apply_a4_format(pil_img):
        """Fuerza una imagen a tener proporciones A4 con borde blanco usando Pillow."""
        w, h = pil_img.size
        is_landscape = w > h
        A4_W, A4_H = 1654, 2339 # Resolución estándar A4 a ~200 DPI
        
        if is_landscape: 
            A4_W, A4_H = 2339, 1654
            
        margin = 60
        target_w = A4_W - (margin * 2)
        target_h = A4_H - (margin * 2)
        
        # Redimensionamos el recorte para que encaje
        resized_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Creamos el lienzo blanco y pegamos la imagen en el centro
        final_img = Image.new("RGB", (A4_W, A4_H), (255, 255, 255))
        final_img.paste(resized_img, (margin, margin))
        return final_img

    def get_processed_image(path, mode, do_auto_crop, thresh_c):
        pil_orig = get_base_image(path)
        if pil_orig is None: return None
        img_to_filter = None
        
        if path in manual_crops:
            l, t, r, b, was_warped = manual_crops[path]
            base_img = pil_orig
            if was_warped:
                if path in cv2_cache: 
                    # FIX: Convertir matriz BGR (OpenCV) a RGB (Pillow)
                    base_img = Image.fromarray(cv2.cvtColor(cv2_cache[path], cv2.COLOR_BGR2RGB))
                else:
                    warped = detect_and_unwarp_document(path)
                    if warped is not None:
                        cv2_cache[path] = warped
                        base_img = Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB))
            
            w_base, h_base = base_img.size
            l, t, r, b = max(0, int(l)), max(0, int(t)), min(w_base, int(r)), min(h_base, int(b))
            
            if r > l and b > t: 
                img_to_filter = base_img.crop((l, t, r, b))
                # === APLICAMOS EL FORMATO A4 AQUÍ ===
                img_to_filter = apply_a4_format(img_to_filter)
            else: 
                img_to_filter = base_img

        elif do_auto_crop:
            if path in cv2_cache: 
                # FIX: Convertir matriz BGR a RGB
                img_to_filter = Image.fromarray(cv2.cvtColor(cv2_cache[path], cv2.COLOR_BGR2RGB))
            else:
                warped = detect_and_unwarp_document(path)
                if warped is not None:
                     cv2_cache[path] = warped
                     img_to_filter = Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB))
                else: img_to_filter = pil_orig

        if img_to_filter is None: img_to_filter = pil_orig

        # === MODO ORIGINAL ===
        if mode == "original":
            return img_to_filter 

        # Si hay filtros, convertimos temporalmente a BGR para que OpenCV trabaje
        cv_final = cv2.cvtColor(np.array(img_to_filter), cv2.COLOR_RGB2BGR)
        if mode == "bw":
            gray = cv2.cvtColor(cv_final, cv2.COLOR_BGR2GRAY)
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, thresh_c)
            cv_final = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        elif mode == "grayscale":
            gray = cv2.cvtColor(cv_final, cv2.COLOR_BGR2GRAY)
            cv_final = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        
        return Image.fromarray(cv_final)

    def get_display_params(pil_img):
        try: cw, ch = preview_canvas.winfo_width(), preview_canvas.winfo_height()
        except: cw, ch = 1, 1
        if cw < 50: cw = 800
        if ch < 50: ch = 600
        w, h = pil_img.size
        scale = min(cw/w, ch/h)
        nw, nh = int(w*scale), int(h*scale)
        x_off, y_off = (cw - nw) // 2, (ch - nh) // 2
        return nw, nh, x_off, y_off, scale

    def update_preview(animate=True):
        nonlocal current_anim_job, last_selected_idx
        if current_anim_job: 
            try: preview_canvas.after_cancel(current_anim_job)
            except: pass
            current_anim_job = None
        preview_canvas.delete("all")

        if not listbox.curselection(): 
            btn_reset_crop.config(state=DISABLED)
            return
        
        idx = listbox.curselection()[0]
        path = image_list[idx]
        if path in manual_crops: btn_reset_crop.config(state=NORMAL)
        else: btn_reset_crop.config(state=DISABLED)

        final_img = get_processed_image(path, mode_var.get(), auto_crop_var.get(), thresh_val.get())
        if not final_img: return

        nw, nh, x_off, y_off, scale = get_display_params(final_img)
        resized_img = final_img.resize((nw, nh), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized_img)
        preview_canvas.image = tk_img 
        preview_canvas.create_image(x_off, y_off, image=tk_img, anchor="nw")
        last_selected_idx = idx

    # --- EVENTOS DEL RATÓN PARA RECORTE ---
    def on_mouse_down(event):
        if not listbox.curselection(): return
        nonlocal crop_start_xy
        crop_start_xy = (event.x, event.y)
        preview_canvas.delete("manual_rect")

    def on_mouse_drag(event):
        if not crop_start_xy: return
        x0, y0 = crop_start_xy
        preview_canvas.delete("manual_rect")
        preview_canvas.create_rectangle(x0, y0, event.x, event.y, outline="#00ff00", width=2, dash=(4, 4), tags="manual_rect")

    def on_mouse_up(event):
        nonlocal crop_start_xy
        if not crop_start_xy or not listbox.curselection(): return
        x0, y0 = crop_start_xy
        x1, y1 = event.x, event.y
        crop_start_xy = None
        preview_canvas.delete("manual_rect")
        if abs(x1 - x0) < 10 or abs(y1 - y0) < 10: return

        idx = listbox.curselection()[0]
        path = image_list[idx]
        img_displayed = get_processed_image(path, mode_var.get(), auto_crop_var.get(), thresh_val.get())
        if not img_displayed: return
        nw, nh, x_off, y_off, scale = get_display_params(img_displayed)

        real_x1 = max(0, (min(x0, x1) - x_off) / scale)
        real_y1 = max(0, (min(y0, y1) - y_off) / scale)
        real_x2 = min(img_displayed.width, (max(x0, x1) - x_off) / scale)
        real_y2 = min(img_displayed.height, (max(y0, y1) - y_off) / scale)

        is_warped_view = (path not in manual_crops and auto_crop_var.get() and path in cv2_cache)
        manual_crops[path] = (real_x1, real_y1, real_x2, real_y2, is_warped_view)
        update_preview(False)

    preview_canvas.bind("<Button-1>", on_mouse_down)
    preview_canvas.bind("<B1-Motion>", on_mouse_drag)
    preview_canvas.bind("<ButtonRelease-1>", on_mouse_up)
    listbox.bind("<<ListboxSelect>>", lambda e: update_preview(True))
    thresh_scale.bind("<ButtonRelease-1>", lambda e: update_preview(False))
    preview_canvas.bind("<Configure>", lambda e: update_preview(False) if listbox.curselection() else None)