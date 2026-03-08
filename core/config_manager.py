# core/config_manager.py
import json
import os

# Definimos la ruta del archivo config.json en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_config():
    """Carga la configuración actual desde el archivo JSON."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error leyendo config.json: {e}")
            return {}
    return {}

def save_config(config_data):
    """Guarda los datos en el archivo JSON."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"Error escribiendo config.json: {e}")

def get_setting(key, default=None):
    """Obtiene un valor de la configuración."""
    config = load_config()
    return config.get(key, default)

def set_setting(key, value):
    """Guarda un nuevo valor en la configuración."""
    config = load_config()
    config[key] = value
    save_config(config)

def get_last_dir():
    """Devuelve la última carpeta utilizada o la carpeta personal del usuario."""
    last_dir = get_setting("last_directory")
    if last_dir and os.path.exists(last_dir):
        return last_dir
    return os.path.expanduser("~") # Carpeta de usuario (Home) por defecto

def set_last_dir(file_path):
    """Extrae la carpeta de un archivo seleccionado y la guarda."""
    if file_path:
        directory = os.path.dirname(file_path)
        set_setting("last_directory", directory)