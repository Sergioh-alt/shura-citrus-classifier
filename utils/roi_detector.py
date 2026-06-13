"""
ROI Detector - Detección automática de región de interés (limón)
Mejora la precisión ignorando fondo y banda transportadora
"""

import cv2
import numpy as np
from typing import Tuple, Optional


class ROIDetector:
    """
    Detector de ROI para limones en imágenes.
    Segmenta automáticamente el limón y extrae solo esa región.
    """
    
    def __init__(self, threshold_method='otsu', min_area_percent=30, max_area_percent=95,
                 expansion_percent=5):
        """
        Args:
            threshold_method: 'otsu' o 'adaptive'
            min_area_percent: Área mínima del limón como % de la imagen (default: 30%)
            max_area_percent: Área máxima del limón como % de la imagen (default: 95%)
            expansion_percent: Expansión del bbox como % para margen (default: 5%)
        """
        self.threshold_method = threshold_method
        self.min_area_percent = min_area_percent
        self.max_area_percent = max_area_percent
        self.expansion_percent = expansion_percent
    
    def detectar_limon(self, imagen: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[Tuple]]:
        """
        Detecta y extrae el limón de la imagen.
        
        Args:
            imagen: Imagen BGR (numpy array)
        
        Returns:
            Tuple de (roi, bbox) donde:
                roi: Imagen recortada del limón (BGR)
                bbox: (x, y, w, h) del bounding box
            Retorna (None, None) si no se detecta limón
        """
        if imagen is None or imagen.size == 0:
            return None, None
        
        height, width = imagen.shape[:2]
        area_total = height * width
        
        # 1. Preprocesamiento
        gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        
        # 2. Reducir ruido
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. Threshold
        if self.threshold_method == 'otsu':
            _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:  # adaptive
            binary = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
        
        # 4. Operaciones morfológicas para limpiar
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # 5. Encontrar contornos
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            print("⚠️  No se detectaron contornos")
            return None, None
        
        # 6. Filtrar contornos por área
        min_area = area_total * self.min_area_percent / 100
        max_area = area_total * self.max_area_percent / 100
        
        valid_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area <= area <= max_area:
                valid_contours.append(cnt)
        
        if not valid_contours:
            print(f"⚠️  No se encontraron contornos válidos (área: {self.min_area_percent}-{self.max_area_percent}%)")
            return None, None
        
        # 7. Seleccionar el contorno más grande
        largest_contour = max(valid_contours, key=cv2.contourArea)
        
        # 8. Obtener bounding box
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # 9. Expandir bbox para margen
        expansion_x = int(w * self.expansion_percent / 100)
        expansion_y = int(h * self.expansion_percent / 100)
        
        x_new = max(0, x - expansion_x)
        y_new = max(0, y - expansion_y)
        w_new = min(width - x_new, w + 2 * expansion_x)
        h_new = min(height - y_new, h + 2 * expansion_y)
        
        bbox = (x_new, y_new, w_new, h_new)
        
        # 10. Extraer ROI
        roi = imagen[y_new:y_new+h_new, x_new:x_new+w_new]
        
        return roi, bbox
    
    def visualizar_deteccion(self, imagen: np.ndarray, bbox: Tuple, 
                            save_path: str = None) -> np.ndarray:
        """
        Visualiza la detección con bbox dibujado.
        
        Args:
            imagen: Imagen original
            bbox: (x, y, w, h)
            save_path: Ruta para guardar (opcional)
        
        Returns:
            Imagen con bbox dibujado
        """
        if bbox is None:
            return imagen.copy()
        
        x, y, w, h = bbox
        imagen_viz = imagen.copy()
        
        # Dibujar bbox
        cv2.rectangle(imagen_viz, (x, y), (x+w, y+h), (0, 255, 0), 3)
        
        # Texto
        cv2.putText(imagen_viz, 'Limon Detectado', (x, y-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if save_path:
            cv2.imwrite(save_path, imagen_viz)
        
        return imagen_viz
    
    def detectar_y_visualizar(self, imagen: np.ndarray, 
                             save_path: str = None) -> Tuple[Optional[np.ndarray], 
                                                             Optional[Tuple],
                                                             np.ndarray]:
        """
        Combina detección y visualización.
        
        Returns:
            (roi, bbox, visualizacion)
        """
        roi, bbox = self.detectar_limon(imagen)
        viz = self.visualizar_deteccion(imagen, bbox, save_path)
        
        return roi, bbox, viz


# Test del ROI Detector
if __name__ == "__main__":
    import sys
    
    print("=== Test de ROI Detector ===\n")
    
    # Cargar imagen de prueba
    imagen_path = "limon_prueba.jpg"
    
    if len(sys.argv) > 1:
        imagen_path = sys.argv[1]
    
    imagen = cv2.imread(imagen_path)
    
    if imagen is None:
        print(f"❌ No se pudo cargar la imagen: {imagen_path}")
        sys.exit(1)
    
    print(f"✓ Imagen cargada: {imagen.shape}")
    
    # Crear detector
    detector = ROIDetector(
        threshold_method='otsu',
        min_area_percent=15,
        max_area_percent=85,
        expansion_percent=10
    )
    
    print("Detectando limón...")
    roi, bbox = detector.detectar_limon(imagen)
    
    if roi is not None:
        x, y, w, h = bbox
        print(f"\n✓ Limón detectado:")
        print(f"  Bounding box: ({x}, {y}, {w}, {h})")
        print(f"  Tamaño ROI: {roi.shape}")
        print(f"  Reducción: {imagen.shape[0]*imagen.shape[1]} → {roi.shape[0]*roi.shape[1]} píxeles")
        print(f"  ({100*(1 - (roi.shape[0]*roi.shape[1])/(imagen.shape[0]*imagen.shape[1])):.1f}% menos)")
        
        # Guardar ROI
        cv2.imwrite('limon_roi.jpg', roi)
        print(f"\n✓ ROI guardado: limon_roi.jpg")
        
        # Visualizar detección
        viz = detector.visualizar_deteccion(imagen, bbox, 'limon_deteccion.jpg')
        print(f"✓ Visualización guardada: limon_deteccion.jpg")
        
        # Comparación
        print("\n📊 Comparación:")
        print(f"  Imagen original: {imagen.shape[1]}x{imagen.shape[0]}")
        print(f"  ROI recortado:   {roi.shape[1]}x{roi.shape[0]}")
        
    else:
        print("\n❌ No se pudo detectar el limón")
        print("   Ajusta los parámetros de min_area_percent y max_area_percent")
    
    print("\n✅ Test completado")
