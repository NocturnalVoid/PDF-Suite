# core/image_processing.py
import cv2
import numpy as np
from PIL import Image

def order_points(pts):
    """Ordena los puntos en: Superior-Izquierda, Superior-Derecha, Inferior-Derecha, Inferior-Izquierda."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def detect_and_unwarp_document(image_path):
    """Detecta el contorno del documento de forma dinámica y lo endereza."""
    try:
        image = cv2.imread(image_path)
        if image is None: return None
        orig = image.copy()
        (H, W) = image.shape[:2]

        # Redimensionar para acelerar el procesamiento sin perder el ratio original
        target_h = 800 
        ratio = H / float(target_h)
        image_resized = cv2.resize(image, (int(W / ratio), target_h))
        area_total = image_resized.shape[0] * image_resized.shape[1]

        # 1. Preprocesamiento más inteligente (Escala de grises y desenfoque ligero)
        gray = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 2. Auto-Canny: Calcula dinámicamente los umbrales según la luz de la foto
        v = np.median(blurred)
        sigma = 0.33
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))
        edged = cv2.Canny(blurred, lower, upper)

        # 3. Cerrar huecos en los bordes (Kernel más pequeño para no fusionar ruidos)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        edged = cv2.dilate(edged, kernel, iterations=1)
        edged = cv2.erode(edged, kernel, iterations=1)

        # 4. Encontrar contornos
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

        screenCnt = None
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            
            # 5. Condición mejorada: Solo necesita ser el 10% del área total de la foto
            if len(approx) == 4:
                if cv2.contourArea(c) > (area_total * 0.10): 
                    screenCnt = approx
                    break

        # Si a pesar de todo no encuentra un rectángulo claro, devuelve la imagen original
        if screenCnt is None: 
            return orig

        # 6. Transformación de perspectiva (Enderezado)
        pts = screenCnt.reshape(4, 2) * ratio
        rect = order_points(pts)
        
        # Expansión sutil para no cortar texto en los bordes (1.025 es 2.5% más grande)
        center = np.mean(rect, axis=0)
        rect = center + (rect - center) * 1.01 
        rect[:, 0] = np.clip(rect[:, 0], 0, W)
        rect[:, 1] = np.clip(rect[:, 1], 0, H)

        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        # Validación de seguridad para evitar recortes diminutos

        dst = np.array([[0, 0],[maxWidth-1, 0],[maxWidth-1, maxHeight-1],[0, maxHeight-1]], dtype="float32")
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))
        
        # === NUEVO: TAMAÑO ESTÁNDAR (A4) Y BORDE BLANCO ===
        # 1. Detectar orientación para no estirar mal la imagen
        is_landscape = maxWidth > maxHeight
        A4_W, A4_H = 1654, 2339 # Resolución estándar A4 a ~200 DPI
        
        if is_landscape:
            A4_W, A4_H = 2339, 1654
            
        margin = 60 # Grosor del borde blanco en píxeles
        
        # 2. Redimensionar el recorte para que quepa dejando espacio para el margen
        target_w = A4_W - (margin * 2)
        target_h = A4_H - (margin * 2)
        
        # INTER_AREA es el mejor algoritmo de OpenCV para ajustar calidad sin pixelar
        warped_resized = cv2.resize(warped, (target_w, target_h), interpolation=cv2.INTER_AREA)
        
        # 3. Añadir el lienzo blanco alrededor (Padding)
        final_scan = cv2.copyMakeBorder(
            warped_resized, 
            top=margin, bottom=margin, left=margin, right=margin, 
            borderType=cv2.BORDER_CONSTANT, 
            value=[255, 255, 255] # Blanco en BGR
        )
        
        return final_scan

    except Exception as e:
        print(f"Error OpenCV: {e}")
        try: return cv2.cvtColor(np.array(Image.open(image_path)), cv2.COLOR_RGB2BGR)
        except: return None