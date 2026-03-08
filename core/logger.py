# core/logger.py
import logging
import os

# Definimos la ruta del archivo log en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "app.log")

def setup_logger():
    """Configura el sistema de logging global de la aplicación."""
    logger = logging.getLogger("UniversalPDFSuite")
    logger.setLevel(logging.DEBUG) 

    # Evitamos duplicar handlers si el módulo se importa varias veces
    if not logger.handlers:
        # Formato profesional: [Fecha y Hora] - [Nivel] - [Archivo:Línea] - [Mensaje]
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

        # 1. Handler para el archivo (Solo guarda advertencias y errores)
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.WARNING) 

        # 2. Handler para la consola (Muestra todo, útil para ti mientras programas)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG) 

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Instancia global lista para ser importada desde cualquier archivo
app_logger = setup_logger()