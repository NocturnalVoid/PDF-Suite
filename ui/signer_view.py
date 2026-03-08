# ui/signer_view.py
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import pdf2image
from tkinter import filedialog as fd, messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont

from ui.utils import setup_window, ejecutar_en_hilo
from core.config_manager import get_last_dir, set_last_dir
from ui.utils import setup_window, ejecutar_en_hilo, native_open_file, native_save_file

def open_sign_pdf_window(root):
    pdf_path = native_open_file(
        title="Selecciona PDF para firmar", 
        initialdir=get_last_dir(),
        filetypes=[("PDF", "*.pdf")]
    )
    if not pdf_path: return
    
    # Validación estricta
    if not pdf_path.lower().endswith(".pdf"):
        messagebox.showerror("Error", "Por favor, selecciona un documento PDF válido.")
        return
        
    set_last_dir(pdf_path)
    root.withdraw()

    annotations = {}
    current_page_idx = 0
    tool_var = "pen" 
    pen_color = "black"
    pen_width = 3
    
    win = tk.Toplevel(root)
    setup_window(win, f"Firmar PDF: {os.path.basename(pdf_path)}", 0.9, 0.9, maximize=True)
    
    # === LÓGICA DE CIERRE ===
    def on_close():
        root.deiconify()
        win.destroy()
        
    win.protocol("WM_DELETE_WINDOW", on_close)

    text_size_var = tk.IntVar(value=40) 
    text_font_var = tk.StringVar(value="arial.ttf")
    draw_start_xy = None
    current_line_points = []

    try:
        pages_images = pdf2image.convert_from_path(pdf_path, dpi=120) 
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo leer el PDF:\n{e}")
        win.destroy()
        return

    total_pages = len(pages_images)

    # ================= LAYOUT PRINCIPAL =================
    sidebar = ttk.Frame(win, width=320, padding=15)
    sidebar.pack(side=LEFT, fill=Y)
    sidebar.pack_propagate(False)

    canvas_frame = ttk.Frame(win, padding=10)
    canvas_frame.pack(side=RIGHT, fill=BOTH, expand=True)

    # ================= SIDEBAR: 1. NAVEGACIÓN =================
    frame_nav = ttk.Labelframe(sidebar, text=" 📄 1. Navegación ", padding=10)
    frame_nav.pack(fill=X, pady=(0, 15))

    lbl_page = ttk.Label(frame_nav, text=f"Página 1 de {total_pages}", font=("Arial", 10, "bold"))
    lbl_page.pack(pady=(0, 10))

    def change_page(delta):
        nonlocal current_page_idx
        new_idx = current_page_idx + delta
        if 0 <= new_idx < total_pages:
            current_page_idx = new_idx
            update_view()

    # === NUEVO: CAMBIO DE PÁGINA CON RUEDA DEL RATÓN ===
    def _on_mousewheel(event):
        if (hasattr(event, 'num') and event.num == 4) or (hasattr(event, 'delta') and event.delta > 0):
            change_page(-1) # Rueda arriba = Página anterior
        elif (hasattr(event, 'num') and event.num == 5) or (hasattr(event, 'delta') and event.delta < 0):
            change_page(1)  # Rueda abajo = Página siguiente

    win.bind("<MouseWheel>", _on_mousewheel)
    win.bind("<Button-4>", _on_mousewheel)
    win.bind("<Button-5>", _on_mousewheel)

    btn_box_nav = ttk.Frame(frame_nav)
    btn_box_nav.pack(fill=X)
    ttk.Button(btn_box_nav, text="<< Anterior", bootstyle="secondary-outline", command=lambda: change_page(-1)).pack(side=LEFT, fill=X, expand=True, padx=(0, 2))
    ttk.Button(btn_box_nav, text="Siguiente >>", bootstyle="secondary-outline", command=lambda: change_page(1)).pack(side=RIGHT, fill=X, expand=True, padx=(2, 0))

    # ================= SIDEBAR: 2. HERRAMIENTAS =================
    frame_tools = ttk.Labelframe(sidebar, text=" 🛠️ 2. Herramientas ", padding=10)
    frame_tools.pack(fill=X, pady=(0, 15))

    def set_tool(t):
        nonlocal tool_var
        tool_var = t
        if t == "pen": 
            canvas.config(cursor="pencil")
            btn_pen.config(bootstyle="primary")
            btn_text.config(bootstyle="primary-outline")
            frame_text_opts.pack_forget() 
        elif t == "text": 
            canvas.config(cursor="xterm")
            btn_pen.config(bootstyle="primary-outline")
            btn_text.config(bootstyle="primary")
            frame_text_opts.pack(fill=X, pady=(10, 0))

    btn_pen = ttk.Button(frame_tools, text="✏️ Lápiz (Firma libre)", bootstyle="primary", command=lambda: set_tool("pen"))
    btn_pen.pack(fill=X, pady=(0, 5))
    
    btn_text = ttk.Button(frame_tools, text="T Insertar Texto", bootstyle="primary-outline", command=lambda: set_tool("text"))
    btn_text.pack(fill=X)

    # ================= SIDEBAR: 3. PROPIEDADES =================
    frame_props = ttk.Labelframe(sidebar, text=" 🎨 3. Propiedades ", padding=10)
    frame_props.pack(fill=X, pady=(0, 15))

    def change_color():
        nonlocal pen_color
        c = colorchooser.askcolor(color=pen_color)[1]
        if c: 
            pen_color = c
            color_swatch.config(bg=c) 

    color_frame = ttk.Frame(frame_props)
    color_frame.pack(fill=X, pady=(0, 5))
    ttk.Button(color_frame, text="Cambiar Color", bootstyle="info-outline", command=change_color).pack(side=LEFT, fill=X, expand=True)
    color_swatch = tk.Label(color_frame, bg=pen_color, width=4, relief="ridge")
    color_swatch.pack(side=RIGHT, padx=(10, 0), fill=Y)

    frame_text_opts = ttk.Frame(frame_props)
    
    ttk.Label(frame_text_opts, text="Tamaño de Letra:").pack(anchor=W, pady=(5, 0))
    ttk.Spinbox(frame_text_opts, from_=8, to=150, textvariable=text_size_var, bootstyle="info").pack(fill=X, pady=(0, 5))
    
    ttk.Label(frame_text_opts, text="Fuente:").pack(anchor=W)
    font_options = ["arial.ttf", "times.ttf", "courier.ttf", "impact.ttf", "DejaVuSans.ttf"]
    ttk.Combobox(frame_text_opts, textvariable=text_font_var, values=font_options, state="readonly", bootstyle="info").pack(fill=X)
    text_font_var.set(font_options[0])

    # ================= SIDEBAR: 4. ACCIONES =================
    frame_actions = ttk.Labelframe(sidebar, text=" 🧹 4. Acciones ", padding=10)
    frame_actions.pack(fill=X, pady=(0, 15))

    def clear_page():
        if current_page_idx in annotations:
            annotations[current_page_idx] = []
            update_view()

    ttk.Button(frame_actions, text="Borrar Dibujos de esta Página", bootstyle="danger-outline", command=clear_page).pack(fill=X)

    # ================= SIDEBAR: GUARDAR (CON HILOS) =================
    def save_signed_pdf():
        save_path = native_save_file(
            title="Guardar PDF firmado",
            initialdir=get_last_dir(),
            defaultextension=".pdf"
        )
        if not save_path: return
        set_last_dir(save_path)

        def tarea_guardar():
            final_images = []
            for idx, pil_img in enumerate(pages_images):
                canvas_img = pil_img.copy().convert("RGB")
                draw = ImageDraw.Draw(canvas_img)
                
                if idx in annotations:
                    for ann in annotations[idx]:
                        if ann['type'] == 'line' and len(ann['points']) > 1:
                            draw.line(ann['points'], fill=ann['color'], width=4, joint="curve")
                        elif ann['type'] == 'text':
                            f_size = ann.get('size', 20)
                            f_name = ann.get('font', "arial.ttf")
                            try: font = ImageFont.truetype(f_name, f_size)
                            except: 
                                try: font = ImageFont.truetype("DejaVuSans.ttf", f_size)
                                except: font = ImageFont.load_default()
                            
                            draw.text(ann['pos'], ann['text'], fill=ann['color'], font=font)
                
                final_images.append(canvas_img)
            
            if final_images:
                final_images[0].save(save_path, save_all=True, append_images=final_images[1:])
            return save_path

        def al_terminar(resultado):
            messagebox.showinfo("Éxito", f"PDF firmado guardado en:\n{resultado}")
            on_close()

        def al_fallar(error):
            messagebox.showerror("Error", f"Ocurrió un error al guardar el PDF:\n{error}")

        ejecutar_en_hilo(
            parent=win,
            tarea_func=tarea_guardar,
            msg_carga="Renderizando firmas y guardando PDF...",
            on_success=al_terminar,
            on_error=al_fallar
        )

    ttk.Button(sidebar, text="GUARDAR PDF FIRMADO", bootstyle="success", padding=15, command=save_signed_pdf).pack(side=BOTTOM, fill=X)

    # ================= ÁREA DE CANVAS (DERECHA) =================
    canvas = tk.Canvas(canvas_frame, bg="#1a1a1a", highlightthickness=1, highlightbackground="#333", cursor="pencil")
    canvas.pack(fill=BOTH, expand=True)

    # --- LÓGICA DE DIBUJO Y VISUALIZACIÓN ---
    def get_scale_and_offset(pil_img):
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if cw < 10: cw, ch = 800, 600
        w, h = pil_img.size
        scale = min(cw/w, ch/h)
        nw, nh = int(w*scale), int(h*scale)
        x_off, y_off = (cw - nw)//2, (ch - nh)//2
        return scale, x_off, y_off, nw, nh

    def update_view():
        canvas.delete("all")
        if current_page_idx >= len(pages_images): return
        
        pil_img = pages_images[current_page_idx]
        lbl_page.config(text=f"Página {current_page_idx+1} de {total_pages}")
        
        scale, x_off, y_off, nw, nh = get_scale_and_offset(pil_img)
        resized = pil_img.resize((nw, nh), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)
        canvas.image = tk_img 
        canvas.create_image(x_off, y_off, image=tk_img, anchor="nw")
        
        if current_page_idx in annotations:
            for ann in annotations[current_page_idx]:
                if ann['type'] == 'line':
                    scaled_pts = []
                    for (x, y) in ann['points']:
                        sx = x * scale + x_off
                        sy = y * scale + y_off
                        scaled_pts.extend([sx, sy])
                    if len(scaled_pts) >= 4:
                        canvas.create_line(scaled_pts, fill=ann['color'], width=pen_width, capstyle=tk.ROUND, smooth=True)
                
                elif ann['type'] == 'text':
                    x, y = ann['pos']
                    sx = x * scale + x_off
                    sy = y * scale + y_off
                    real_size = ann.get('size', 20)
                    display_size = max(8, int(real_size * scale))
                    
                    canvas.create_text(sx, sy, text=ann['text'], fill=ann['color'], 
                                     font=("Helvetica", display_size, "bold"), anchor="w")

    def on_mousedown(event):
        nonlocal current_line_points
        if current_page_idx >= len(pages_images): return
        pil_img = pages_images[current_page_idx]
        scale, x_off, y_off, nw, nh = get_scale_and_offset(pil_img)
        
        rx = (event.x - x_off) / scale
        ry = (event.y - y_off) / scale
        
        if tool_var == "pen":
            current_line_points = [(rx, ry)]
        elif tool_var == "text":
            txt = simpledialog.askstring("Texto", "Escribe el texto:")
            if txt:
                if current_page_idx not in annotations: annotations[current_page_idx] = []
                annotations[current_page_idx].append({
                    'type': 'text', 'text': txt, 'pos': (rx, ry), 
                    'color': pen_color, 'font': text_font_var.get(), 'size': int(text_size_var.get())
                })
                update_view()

    def on_drag(event):
        nonlocal current_line_points
        if tool_var != "pen": return
        pil_img = pages_images[current_page_idx]
        scale, x_off, y_off, nw, nh = get_scale_and_offset(pil_img)
        
        rx = (event.x - x_off) / scale
        ry = (event.y - y_off) / scale
        current_line_points.append((rx, ry))
        
        if len(current_line_points) >= 2:
            x1, y1 = current_line_points[-2]
            x2, y2 = current_line_points[-1]
            sx1, sy1 = x1*scale + x_off, y1*scale + y_off
            sx2, sy2 = x2*scale + x_off, y2*scale + y_off
            canvas.create_line(sx1, sy1, sx2, sy2, fill=pen_color, width=pen_width, capstyle=tk.ROUND)

    def on_mouseup(event):
        nonlocal current_line_points
        if tool_var == "pen" and len(current_line_points) > 1:
            if current_page_idx not in annotations: annotations[current_page_idx] = []
            annotations[current_page_idx].append({
                'type': 'line', 'points': list(current_line_points), 'color': pen_color
            })
            current_line_points = []
            update_view()

    canvas.bind("<Button-1>", on_mousedown)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_mouseup)
    canvas.bind("<Configure>", lambda e: update_view())