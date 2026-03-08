# 📄 Universal PDF Suite

Una potente y moderna suite de escritorio desarrollada en Python para la gestión integral de documentos PDF y procesamiento de imágenes. Diseñada bajo una estricta arquitectura MVC, la aplicación garantiza fluidez mediante procesamiento asíncrono y cuenta con integración nativa de diálogos para entornos Linux y Windows.

---

## ✨ Características Principales

La suite se compone de cinco herramientas independientes y altamente optimizadas:

* **✂️ Editor de PDF:** Permite visualizar, reordenar (mover adelante/atrás), rotar y eliminar páginas específicas de un documento sin corromper metadatos, utilizando un sistema de mapeo de índices original.
* **📷 Escáner Inteligente (Visión Artificial):** Utiliza OpenCV para detectar bordes de documentos en fotografías (Auto-Canny), aplicando transformaciones de perspectiva para enderezar la imagen. Estandariza el resultado a formato A4 (~200 DPI) con márgenes profesionales. Incluye filtros de Blanco/Negro (Umbral Adaptativo), Escala de Grises y Color Original.
* **✍️ Firmante de PDF:** Un lienzo interactivo para dibujar firmas a mano alzada o insertar texto mecanografiado sobre páginas específicas. Soporta selección dinámica de colores, fuentes y grosores de trazo.
* **🔗 Unificador de PDF (Merger):** Herramienta optimizada para combinar múltiples archivos PDF con controles visuales intuitivos para reordenar la secuencia final antes de la unión.
* **🔄 Conversor DOCX a PDF:** Motor de conversión directa. En entornos Linux (Debian/Ubuntu) interactúa nativamente con `libreoffice --headless`, garantizando máxima fidelidad en el formato.

---

## 🏗️ Arquitectura y Tecnologías

El proyecto sigue el patrón **Modelo-Vista-Controlador (MVC)**, asegurando la separación de la lógica de negocio y la interfaz gráfica.

* **Frontend:** `tkinter` + `ttkbootstrap` (Tema oscuro moderno 'Darkly').
* **Backend (Motor PDF):** `pypdf`, `pdf2image`.
* **Visión Artificial:** `opencv-python` (`cv2`), `numpy`, `Pillow`.
* **Concurrencia:** Sistema de hilos (`threading`) para evitar el bloqueo de la interfaz gráfica durante el renderizado pesado.
* **Integración OS:** Interceptores personalizados (`zenity` via `subprocess`) para forzar exploradores de archivos nativos en distribuciones Linux.

---

## 🚀 Instalación y Despliegue

Sigue estos pasos para clonar y ejecutar el entorno localmente. Se recomienda encarecidamente el uso de un entorno virtual.

### 1. Clonar el repositorio
```bash
git clone [https://github.com/NocturnalVoid/PDF-Suite.git](https://github.com/NocturnalVoid/PDF-Suite.git)
cd PDF-Suite
