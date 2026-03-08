# controllers/pdf_ctrl.py
import tkinter as tk
from tkinter import messagebox
from core.pdf_engine import merge_pdfs, convert_docx_to_pdf
from ui.utils import ejecutar_en_hilo, native_open_file, native_save_file
from core.config_manager import get_last_dir, set_last_dir

def handle_merge_pdfs(pdf_list):
    """Controlador para la acción de unir PDFs."""
    if not pdf_list:
        messagebox.showwarning("Atención", "Agrega al menos un PDF a la lista.")
        return
        
    output_path = native_save_file(
        title="Guardar PDF Unido",
        initialdir=get_last_dir(),
        defaultextension=".pdf"
    )
    
    if output_path:
        set_last_dir(output_path)
        try:
            merge_pdfs(pdf_list, output_path)
            messagebox.showinfo("Éxito", "Los archivos PDF se han unido correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al unir los archivos:\n{e}")

def handle_docx_to_pdf():
    # 1. Usar el explorador nativo para ABRIR
    docx_path = native_open_file(
        title="Selecciona el archivo Word", 
        initialdir=get_last_dir(),
        filetypes=[("Word Documents", "*.docx")]
    )
    if not docx_path: return
    
    # Validación estricta para proteger el Motor
    if not docx_path.lower().endswith(".docx"):
        messagebox.showerror("Archivo no válido", "Por favor, selecciona un documento .docx válido.")
        return
        
    set_last_dir(docx_path) 

    # 2. Usar el explorador nativo para GUARDAR
    pdf_path = native_save_file(
        title="Guardar PDF como...", 
        initialdir=get_last_dir(),
        defaultextension=".pdf"
    )
    if not pdf_path: return
    set_last_dir(pdf_path) 

    # 3. Lógica de Hilos (Intacta)
    def tarea_pesada():
        convert_docx_to_pdf(docx_path, pdf_path)
        return pdf_path

    def al_terminar(resultado):
        messagebox.showinfo("Éxito", f"Documento convertido exitosamente:\n{resultado}")

    def al_fallar(error):
        messagebox.showerror("Error", f"Fallo al convertir el documento:\n{error}")

    root = tk._default_root
    ejecutar_en_hilo(
        parent=root,
        tarea_func=tarea_pesada,
        msg_carga="Convirtiendo de Word a PDF...\nEsto puede tardar unos segundos.",
        on_success=al_terminar,
        on_error=al_fallar
    )