"""
Gestor de Configuración del Sistema de Clasificación de Limones
Carga, guarda y valida parámetros desde archivo JSON
"""

import json
import os
from typing import Dict, Any
from pathlib import Path


class ConfigManager:
    """
    Administra la configuración del sistema de clasificación.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_path: Ruta al archivo de configuración JSON
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> bool:
        """
        Carga la configuración desde el archivo JSON.
        
        Returns:
            True si la carga fue exitosa, False en caso contrario
        """
        try:
            if not os.path.exists(self.config_path):
                print(f"[WARN] Archivo de configuracion no encontrado: {self.config_path}")
                print("   Creando configuracion por defecto...")
                self.create_default_config()
                return True
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Validar configuración
            if self.validate():
                return True
            else:
                print("❌ Configuración inválida, usando valores por defecto")
                self.create_default_config()
                return False
                
        except Exception as e:
            print(f"❌ Error al cargar configuración: {e}")
            self.create_default_config()
            return False
    
    def save(self) -> bool:
        """
        Guarda la configuración actual al archivo JSON.
        
        Returns:
            True si el guardado fue exitoso
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error al guardar configuración: {e}")
            return False
    
    def validate(self) -> bool:
        """
        Valida que la configuración tenga todos los campos necesarios.
        
        Returns:
            True si la configuración es válida
        """
        required_keys = [
            'version',
            'clasificacion',
            'vida_util',
            'visualizacion'
        ]
        
        for key in required_keys:
            if key not in self.config:
                print(f"[WARN] Falta clave requerida: {key}")
                return False
        
        return True
    
    def create_default_config(self):
        """
        Crea y guarda una configuración por defecto.
        """
        self.config = {
            "version": "1.0",
            "clasificacion": {
                "tonalidad": {
                    "verde": {
                        "min": 35,
                        "max": 85,
                        "descripcion": "Inmaduro - Alta acidez"
                    },
                    "pinton": {
                        "min": 20,
                        "max": 34,
                        "descripcion": "Maduración media - Transición"
                    },
                    "amarillo": {
                        "min": 0,
                        "max": 19,
                        "descripcion": "Maduro - Óptimo consumo"
                    }
                },
                "rugosidad": {
                    "umbral_exportacion": 50.0,
                    "descripcion": "Coeficiente máximo de rugosidad para exportación larga"
                },
                "defectos": {
                    "porcentaje_maximo": 5.0,
                    "umbral_deteccion": 100.0,
                    "descripcion": "Porcentaje máximo de defectos superficiales aceptable"
                }
            },
            "vida_util": {
                "exportacion_larga": {
                    "dias": 30,
                    "criterios": {
                        "tonalidad_minima": 20,
                        "rugosidad_maxima": 50.0,
                        "defectos_maximos": 5.0
                    }
                },
                "consumo_local": {
                    "dias": 7,
                    "descripcion": "No cumple criterios de exportación larga"
                }
            },
            "visualizacion": {
                "colores": {
                    "exportacion": [0, 200, 0],
                    "consumo_local": [255, 165, 0]
                },
                "dpi_salida": 150
            }
        }
        self.save()
    
    # Métodos de acceso a parámetros específicos
    
    def get_tonalidad_rangos(self) -> Dict:
        """Obtiene los rangos de tonalidad para clasificación"""
        return self.config['clasificacion']['tonalidad']
    
    def get_rugosidad_umbral(self) -> float:
        """Obtiene el umbral de rugosidad para exportación"""
        return self.config['clasificacion']['rugosidad']['umbral_exportacion']
    
    def get_defectos_maximo(self) -> float:
        """Obtiene el porcentaje máximo de defectos aceptable"""
        return self.config['clasificacion']['defectos']['porcentaje_maximo']
    
    def get_defectos_umbral_deteccion(self) -> float:
        """Obtiene el umbral de intensidad para detectar defectos"""
        return self.config['clasificacion']['defectos']['umbral_deteccion']
    
    def get_criterios_exportacion(self) -> Dict:
        """Obtiene todos los criterios para exportación larga"""
        return self.config['vida_util']['exportacion_larga']['criterios']
    
    def get_dias_vida_util(self, categoria: str) -> int:
        """
        Obtiene los días de vida útil para una categoría.
        
        Args:
            categoria: 'exportacion_larga' o 'consumo_local'
        """
        return self.config['vida_util'][categoria]['dias']
    
    def get_color_etiqueta(self, categoria: str) -> tuple:
        """
        Obtiene el color RGB para una categoría de etiqueta.
        
        Args:
            categoria: 'exportacion' o 'consumo_local'
        """
        color = self.config['visualizacion']['colores'][categoria]
        return tuple(color)
    
    # Métodos para modificar parámetros
    
    def set_tonalidad_rango(self, categoria: str, min_val: float, max_val: float):
        """Establece el rango de tonalidad para una categoría"""
        if categoria in self.config['clasificacion']['tonalidad']:
            self.config['clasificacion']['tonalidad'][categoria]['min'] = min_val
            self.config['clasificacion']['tonalidad'][categoria]['max'] = max_val
    
    def set_rugosidad_umbral(self, valor: float):
        """Establece el umbral de rugosidad"""
        self.config['clasificacion']['rugosidad']['umbral_exportacion'] = valor
        self.config['vida_util']['exportacion_larga']['criterios']['rugosidad_maxima'] = valor
    
    def set_defectos_maximo(self, valor: float):
        """Establece el porcentaje máximo de defectos"""
        self.config['clasificacion']['defectos']['porcentaje_maximo'] = valor
        self.config['vida_util']['exportacion_larga']['criterios']['defectos_maximos'] = valor
    
    def export_config(self, output_path: str = "config_backup.json"):
        """Exporta la configuración actual a un archivo de respaldo"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error al exportar configuración: {e}")
            return False
    
    def import_config(self, config_path: str) -> bool:
        """Importa configuración desde un archivo externo"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            self.config = imported_config
            if self.validate():
                self.save()
                return True
            else:
                print("❌ Configuración importada inválida")
                return False
        except Exception as e:
            print(f"❌ Error al importar configuración: {e}")
            return False


# Ejemplo de uso
if __name__ == "__main__":
    config = ConfigManager()
    
    print(f"Rangos de tonalidad: {config.get_tonalidad_rangos()}")
    print(f"Umbral de rugosidad: {config.get_rugosidad_umbral()}")
    print(f"Defectos máximos: {config.get_defectos_maximo()}%")
    print(f"Criterios exportación: {config.get_criterios_exportacion()}")
