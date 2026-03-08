# core/pdf_engine.py
import os
import platform
import subprocess
import shutil
from pypdf import PdfReader, PdfWriter

# Verificar docx2pdf
try:
    from docx2pdf import convert as docx2pdf_convert
    HAS_DOCX2PDF = True
except ImportError:
    HAS_DOCX2PDF = False


def merge_pdfs(input_paths, output_path):
    """Une una lista de rutas de PDFs en un solo archivo de salida."""
    if not input_paths:
        raise ValueError("La lista de archivos PDF está vacía.")
    
    merger = PdfWriter()
    for path in input_paths:
        merger.append(path)
        
    with open(output_path, "wb") as out_file:
        merger.write(out_file)
        
    return output_path


def convert_docx_to_pdf(input_path, output_path):
    """Convierte un archivo DOCX a PDF usando docx2pdf (Windows) o LibreOffice (Linux/Mac)."""
    if platform.system() == "Windows" and HAS_DOCX2PDF:
        docx2pdf_convert(input_path, output_path)
    else:
        # Comando para sistemas basados en Unix (ej. Debian/Ubuntu) usando LibreOffice
        out_dir = os.path.dirname(output_path)
        cmd = ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", out_dir, input_path]
        subprocess.run(cmd, check=True)
        
        # LibreOffice nombra el archivo automáticamente, lo renombramos si es necesario
        gen_name = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
        gen_path = os.path.join(out_dir, gen_name)
        
        if gen_path != output_path and os.path.exists(gen_path):
            shutil.move(gen_path, output_path)
            
    return output_path


def save_edited_pdf(input_path, output_path, pages_data, rotations, password=None):
    """Crea un nuevo PDF basándose en el orden de páginas y rotaciones especificadas."""
    reader = PdfReader(input_path)
    if password:
        reader.decrypt(password) # Desencriptar antes de extraer las páginas
        
    writer = PdfWriter()
    
    for idx in pages_data:
        page = reader.pages[idx]
        angle = rotations.get(idx, 0)
        if angle != 0: 
            page.rotate(-angle) 
        writer.add_page(page)
        
    with open(output_path, "wb") as f:
        writer.write(f)
        
    return output_path