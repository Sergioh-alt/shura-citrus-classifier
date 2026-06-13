"""
Clasificador de Limones - Módulo Core
Versión refactorizada con soporte para configuración dinámica
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
from typing import Tuple, Dict, Optional
from core.config_manager import ConfigManager


class ClasificadorLimones:
    """
    Clase principal para clasificación de limones basada en análisis cromático y morfológico.
    Utiliza ConfigManager para parámetros ajustables.
    """
    
    def __init__(self, ruta_imagen: str = None, config_manager: ConfigManager = None, verbose: bool = True):
        """
        Inicializa el clasificador con una imagen de entrada.
        
        Args:
            ruta_imagen: Ruta al archivo de imagen a procesar (opcional para uso en GUI)
            config_manager: Instancia de ConfigManager (se crea uno nuevo si es None)
            verbose: Si True, imprime información detallada durante el procesamiento
        """
        self.ruta_imagen = ruta_imagen
        self.config = config_manager if config_manager else ConfigManager()
        self.verbose = verbose
        
        # Tensores y matrices
        self.imagen_rgb = None
        self.tensor_original = None
        self.M_R = None  # Matriz de canal Rojo
        self.M_G = None  # Matriz de canal Verde
        self.M_B = None  # Matriz de canal Azul
        self.imagen_hsv = None
        self.M_H = None  # Matriz de Tonalidad (Hue)
        self.bordes = None
        
        # Resultados
        self.vector_caracteristicas = None
        self.clasificacion = None
        self.categoria_maduracion = None
        
    def _print(self, *args, **kwargs):
        """Imprime solo si verbose está activo"""
        if self.verbose:
            print(*args, **kwargs)
    
    def cargar_imagen(self, ruta_imagen: str = None) -> bool:
        """
        Módulo de Entrada de Datos: Carga la imagen y la descompone en tensor 3D.
        
        Args:
            ruta_imagen: Ruta a la imagen (usa self.ruta_imagen si es None)
        
        Returns:
            True si la carga fue exitosa, False en caso contrario
        """
        if ruta_imagen:
            self.ruta_imagen = ruta_imagen
            
        try:
            # Cargar imagen usando OpenCV (formato BGR por defecto)
            imagen_bgr = cv2.imread(self.ruta_imagen)
            
            if imagen_bgr is None:
                self._print(f"❌ Error: No se pudo cargar la imagen desde '{self.ruta_imagen}'")
                return False
            
            # Convertir de BGR a RGB para procesamiento estándar
            self.imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
            
            # Representar como tensor de orden 3: m×n×3
            self.tensor_original = self.imagen_rgb.astype(np.float32)
            
            # Descomposición matricial en tres planos de color
            self.M_R = self.tensor_original[:, :, 0]  # Canal Rojo
            self.M_G = self.tensor_original[:, :, 1]  # Canal Verde
            self.M_B = self.tensor_original[:, :, 2]  # Canal Azul
            
            m, n, canales = self.tensor_original.shape
            self._print(f"✓ Imagen cargada exitosamente")
            self._print(f"  Dimensiones del tensor: {m} × {n} × {canales}")
            self._print(f"  Tamaño total: {m * n * canales:,} valores")
            
            return True
            
        except Exception as e:
            self._print(f"❌ Error al cargar imagen: {e}")
            return False
    
    def cargar_desde_array(self, imagen_array: np.ndarray) -> bool:
        """
        Carga imagen desde un numpy array (útil para GUI).
        
        Args:
            imagen_array: Imagen como numpy array en formato RGB
        
        Returns:
            True si la carga fue exitosa
        """
        try:
            self.imagen_rgb = imagen_array
            self.tensor_original = self.imagen_rgb.astype(np.float32)
            
            # Descomposición matricial
            self.M_R = self.tensor_original[:, :, 0]
            self.M_G = self.tensor_original[:, :, 1]
            self.M_B = self.tensor_original[:, :, 2]
            
            m, n, canales = self.tensor_original.shape
            self._print(f"✓ Imagen cargada desde array")
            self._print(f"  Dimensiones: {m} × {n} × {canales}")
            
            return True
        except Exception as e:
            self._print(f"❌ Error al cargar desde array: {e}")
            return False
    
    def transformacion_rgb_a_hsv(self):
        """
        Módulo Cromático: Implementa transformación lineal RGB → HSV.
        Utiliza configuración para clasificación posterior.
        """
        # Normalizar valores RGB al rango [0, 1]
        imagen_normalizada = self.tensor_original / 255.0
        
        # Aplicar transformación RGB → HSV
        self.imagen_hsv = cv2.cvtColor(imagen_normalizada.astype(np.float32), cv2.COLOR_RGB2HSV)
        
        # Extraer matriz de Tonalidad (H)
        self.M_H = self.imagen_hsv[:, :, 0]
        
        self._print(f"\n{'='*60}")
        self._print(f"MÓDULO CROMÁTICO - Análisis de Tonalidad")
        self._print(f"{'='*60}")
        self._print(f"  Rango de Tonalidad (H): [{self.M_H.min():.2f}, {self.M_H.max():.2f}]")
        self._print(f"  Promedio de Tonalidad: {self.M_H.mean():.2f}°")
        self._print(f"  Desviación estándar: {self.M_H.std():.2f}°")
    
    def calcular_acidez_estimada(self) -> float:
        """
        Estima el porcentaje de acidez basado en la tonalidad y saturación.
        
        Metodología:
        - Regresión lineal inversa: H alto → acidez alta
        - Ajuste por saturación: mayor saturación → menor acidez
        - Basado en correlación color-pH en cítricos
        
        Returns:
            Porcentaje estimado de acidez (2-8%)
        """
        H_avg = self.M_H.mean()
        S_avg = self.imagen_hsv[:, :, 1].mean()
        
        # Modelo de regresión lineal inversa por rangos
        if H_avg >= 35:  # Verde
            # Rango H: [35, 85] → Acidez base: [8%, 6%]
            acidez_base = 8.0 - ((H_avg - 35) / 50) * 2.0
        elif H_avg >= 20:  # Pintón
            # Rango H: [20, 34] → Acidez base: [6%, 4%]
            acidez_base = 6.0 - ((H_avg - 20) / 14) * 2.0
        else:  # Amarillo
            # Rango H: [0, 19] → Acidez base: [4%, 2%]
            acidez_base = 4.0 - (H_avg / 19) * 2.0
        
        # Ajuste por saturación (limones más saturados tienden a ser menos ácidos)
        factor_saturacion = 1.0 + (0.5 - S_avg) * 0.2
        acidez_estimada = max(2.0, min(8.0, acidez_base * factor_saturacion))
        
        self._print(f"  🧪 Acidez Estimada: {acidez_estimada:.2f}%")
        
        return acidez_estimada
    
    def clasificar_maduracion(self) -> str:
        """
        Clasifica el limón según umbrales configurables en el espacio de tonalidad.
        
        Returns:
            Categoría de maduración como string
        """
        promedio_h = self.M_H.mean()
        
        # Obtener rangos desde la configuración
        tonalidad_config = self.config.get_tonalidad_rangos()
        
        # Clasificación dinámica basada en configuración
        if tonalidad_config['verde']['min'] <= promedio_h <= tonalidad_config['verde']['max']:
            categoria = "Verde"
            descripcion = tonalidad_config['verde']['descripcion']
        elif tonalidad_config['pinton']['min'] <= promedio_h < tonalidad_config['pinton']['max']:
            categoria = "Pintón"
            descripcion = tonalidad_config['pinton']['descripcion']
        else:
            categoria = "Amarillo"
            descripcion = tonalidad_config['amarillo']['descripcion']
        
        self.categoria_maduracion = categoria
        
        self._print(f"\n  [INFO] Clasificacion Cromatica: {categoria}")
        self._print(f"     {descripcion}")
        
        return categoria
    
    def deteccion_bordes_sobel(self):
        """
        Módulo Morfológico: Aplica convolución matricial para detectar bordes.
        """
        # Convertir a escala de grises
        imagen_gris = cv2.cvtColor(self.imagen_rgb, cv2.COLOR_RGB2GRAY)
        
        self._print(f"\n{'='*60}")
        self._print(f"MÓDULO MORFOLÓGICO - Detección de Imperfecciones")
        self._print(f"{'='*60}")
        
        # Aplicar operador de Sobel
        sobel_x = cv2.Sobel(imagen_gris, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(imagen_gris, cv2.CV_64F, 0, 1, ksize=3)
        
        # Calcular magnitud del gradiente
        self.bordes = np.sqrt(sobel_x**2 + sobel_y**2)
        
        # Estadísticas
        self._print(f"  Intensidad de bordes (promedio): {self.bordes.mean():.2f}")
        self._print(f"  Intensidad máxima: {self.bordes.max():.2f}")
        
        # Normalizar para visualización
        bordes_norm = cv2.normalize(self.bordes, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return bordes_norm
    
    def calcular_rugosidad(self) -> float:
        """
        Calcula coeficiente de rugosidad basado en varianza de gradientes.
        
        Returns:
            Coeficiente de rugosidad
        """
        varianza = np.var(self.bordes)
        promedio = np.mean(self.bordes) + 1e-6
        
        coeficiente = varianza / promedio
        
        self._print(f"  Coeficiente de Rugosidad: {coeficiente:.4f}")
        
        return coeficiente
    
    def calcular_porcentaje_defectos(self, umbral: float = None) -> float:
        """
        Calcula porcentaje de área con defectos superficiales.
        
        Args:
            umbral: Valor de intensidad (usa configuración si es None)
        
        Returns:
            Porcentaje de píxeles defectuosos
        """
        if umbral is None:
            umbral = self.config.get_defectos_umbral_deteccion()
        
        pixeles_defectuosos = np.sum(self.bordes > umbral)
        total_pixeles = self.bordes.size
        
        porcentaje = (pixeles_defectuosos / total_pixeles) * 100
        
        self._print(f"  Porcentaje de Defectos Superficiales: {porcentaje:.2f}%")
        
        return porcentaje
    
    def generar_vector_caracteristicas(self) -> np.ndarray:
        """
        Genera vector de características para clasificación final.
        
        Returns:
            Vector de características v ∈ ℝ³
        """
        # Clasificar maduración primero
        categoria_maduracion = self.clasificar_maduracion()
        
        # Calcular métricas
        rugosidad = self.calcular_rugosidad()
        defectos = self.calcular_porcentaje_defectos()
        
        # Construir vector
        self.vector_caracteristicas = np.array([
            self.M_H.mean(),  # Promedio de Tonalidad
            rugosidad,        # Coeficiente de Rugosidad
            defectos          # % Defectos Superficiales
        ])
        
        self._print(f"\n{'='*60}")
        self._print(f"VECTOR DE CARACTERÍSTICAS")
        self._print(f"{'='*60}")
        self._print(f"  v = [{self.vector_caracteristicas[0]:.2f}, "
              f"{self.vector_caracteristicas[1]:.4f}, "
              f"{self.vector_caracteristicas[2]:.2f}]ᵀ")
        
        return self.vector_caracteristicas
    
    def clasificar_calidad(self) -> Dict[str, any]:
        """
        Lógica de Negocio: Clasifica según vida útil estimada.
        Utiliza criterios configurables.
        
        Returns:
            Diccionario con clasificación y justificación
        """
        H_avg, rugosidad, defectos = self.vector_caracteristicas
        
        self._print(f"\n{'='*60}")
        self._print(f"CLASIFICACIÓN DE CALIDAD Y VIDA ÚTIL")
        self._print(f"{'='*60}")
        
        # Obtener criterios desde configuración
        criterios = self.config.get_criterios_exportacion()
        
        # Evaluar criterios
        maduracion_apropiada = H_avg >= criterios['tonalidad_minima']
        calidad_superficial = (rugosidad < criterios['rugosidad_maxima']) and \
                             (defectos < criterios['defectos_maximos'])
        
        # Decisión final
        if maduracion_apropiada and calidad_superficial:
            clasificacion = "APTO PARA EXPORTACIÓN LARGA"
            vida_util = f"{self.config.get_dias_vida_util('exportacion_larga')} días"
            justificacion = "Cumple todos los criterios de calidad premium"
            color_etiqueta = self.config.get_color_etiqueta('exportacion')
        else:
            clasificacion = "CONSUMO LOCAL"
            vida_util = f"{self.config.get_dias_vida_util('consumo_local')} días"
            
            # Generar justificación específica
            razones = []
            if not maduracion_apropiada:
                razones.append(f"Tonalidad inadecuada ({H_avg:.2f}° < {criterios['tonalidad_minima']}°)")
            if rugosidad >= criterios['rugosidad_maxima']:
                razones.append(f"Alta rugosidad ({rugosidad:.2f})")
            if defectos >= criterios['defectos_maximos']:
                razones.append(f"Defectos superficiales ({defectos:.2f}%)")
            
            justificacion = "; ".join(razones)
            color_etiqueta = self.config.get_color_etiqueta('consumo_local')
        
        self.clasificacion = {
            'categoria': clasificacion,
            'vida_util': vida_util,
            'justificacion': justificacion,
            'color_etiqueta': color_etiqueta,
            'cumple_exportacion': maduracion_apropiada and calidad_superficial
        }
        
        # Mostrar resultados
        self._print(f"  [INFO] Clasificacion: {clasificacion}")
        self._print(f"  [INFO] Vida Util Estimada: {vida_util}")
        self._print(f"  [INFO] Justificacion: {justificacion}")
        
        return self.clasificacion
    
    def visualizar_resultados(self, guardar: bool = True, mostrar: bool = True) -> Optional[str]:
        """
        Genera visualización completa de resultados con múltiples paneles.
        
        Args:
            guardar: Si True, guarda la imagen en disco
            mostrar: Si True, muestra la ventana de matplotlib
        
        Returns:
            Ruta del archivo guardado (si guardar=True)
        """
        # Crear figura con 4 subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Sistema de Clasificación de Limones - Análisis Completo', 
                     fontsize=16, fontweight='bold')
        
        # Panel 1: Imagen Original
        axes[0, 0].imshow(self.imagen_rgb)
        axes[0, 0].set_title('Imagen Original (RGB)', fontsize=12, fontweight='bold')
        axes[0, 0].axis('off')
        
        # Panel 2: Mapa de Tonalidad
        im_h = axes[0, 1].imshow(self.M_H, cmap='hsv')
        axes[0, 1].set_title('Mapa de Tonalidad (H) - Análisis Cromático', 
                             fontsize=12, fontweight='bold')
        axes[0, 1].axis('off')
        plt.colorbar(im_h, ax=axes[0, 1], label='Tonalidad (grados)')
        
        # Panel 3: Bordes Detectados
        bordes_viz = cv2.normalize(self.bordes, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        axes[1, 0].imshow(bordes_viz, cmap='hot')
        axes[1, 0].set_title('Detección de Bordes (Sobel) - Análisis Morfológico', 
                            fontsize=12, fontweight='bold')
        axes[1, 0].axis('off')
        
        # Panel 4: Clasificación Final
        imagen_etiquetada = self.imagen_rgb.copy()
        altura, ancho = imagen_etiquetada.shape[:2]
        
        texto = f"{self.clasificacion['categoria']}"
        subtexto = f"Vida útil: {self.clasificacion['vida_util']}"
        
        # Fondo semi-transparente
        overlay = imagen_etiquetada.copy()
        cv2.rectangle(overlay, (10, altura - 120), (ancho - 10, altura - 10), 
                     self.clasificacion['color_etiqueta'], -1)
        imagen_etiquetada = cv2.addWeighted(overlay, 0.7, imagen_etiquetada, 0.3, 0)
        
        # Texto
        cv2.putText(imagen_etiquetada, texto, (20, altura - 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(imagen_etiquetada, subtexto, (20, altura - 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        
        axes[1, 1].imshow(imagen_etiquetada)
        axes[1, 1].set_title('Clasificación Final', fontsize=12, fontweight='bold')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        
        # Guardar
        nombre_salida = None
        if guardar and self.ruta_imagen:
            nombre_salida = self.ruta_imagen.replace('.', '_resultado.')
            dpi = self.config.config['visualizacion']['dpi_salida']
            plt.savefig(nombre_salida, dpi=dpi, bbox_inches='tight')
            self._print(f"\n✓ Visualización guardada en: {nombre_salida}")
        
        # Mostrar
        if mostrar:
            plt.show()
        else:
            plt.close(fig)
        
        return nombre_salida
    
    def procesar(self, mostrar_visualizacion: bool = True) -> Dict:
        """
        Pipeline completo de procesamiento.
        
        Args:
            mostrar_visualizacion: Si True, muestra ventana de matplotlib
        
        Returns:
            Diccionario con todos los resultados
        """
        self._print(f"\n{'#'*60}")
        self._print(f"# SISTEMA DE CLASIFICACIÓN DE LIMONES PARA EXPORTACIÓN")
        self._print(f"# Basado en Álgebra Lineal y Visión por Computadora")
        self._print(f"{'#'*60}\n")
        
        # Pipeline
        if self.imagen_rgb is None:
            if not self.cargar_imagen():
                return None
        
        self.transformacion_rgb_a_hsv()
        self.deteccion_bordes_sobel()
        self.generar_vector_caracteristicas()
        self.clasificar_calidad()
        
        # Visualización
        self._print(f"\n{'='*60}")
        self._print(f"Generando visualización...")
        self._print(f"{'='*60}")
        archivo_salida = self.visualizar_resultados(mostrar=mostrar_visualizacion)
        
        # Calcular acidez
        acidez = self.calcular_acidez_estimada()
        
        self._print(f"\n{'#'*60}")
        self._print(f"# PROCESAMIENTO COMPLETADO")
        self._print(f"{'#'*60}\n")
        
        # Retornar resultados completos
        return {
            'vector_caracteristicas': self.vector_caracteristicas,
            'clasificacion': self.clasificacion,
            'categoria_maduracion': self.categoria_maduracion,
            'acidez_estimada': acidez,
            'archivo_salida': archivo_salida,
            'dimensiones': self.tensor_original.shape if self.tensor_original is not None else None
        }
