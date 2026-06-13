"""
Exportadores de datos para el Sistema de Clasificación de Limones
Soporta múltiples formatos: CSV, JSON, y en futuro PDF
"""

import json
import csv
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class DataExporter:
    """
    Clase para exportar resultados de clasificación a diferentes formatos.
    """
    
    @staticmethod
    def exportar_csv(resultados: List[Dict], ruta_salida: str) -> bool:
        """
        Exporta resultados a formato CSV.
        
        Args:
            resultados: Lista de diccionarios con resultados de clasificación
            ruta_salida: Ruta del archivo CSV de salida
        
        Returns:
            True si la exportación fue exitosa
        """
        try:
            with open(ruta_salida, 'w', newline='', encoding='utf-8') as f:
                if not resultados:
                    return False
                
                fieldnames = [
                    'archivo',
                    'fecha_analisis',
                    'tonalidad_promedio',
                    'categoria_maduracion',
                    'rugosidad',
                    'defectos_porcentaje',
                    'clasificacion',
                    'vida_util_dias',
                    'justificacion'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for resultado in resultados:
                    writer.writerow({
                        'archivo': resultado.get('archivo', ''),
                        'fecha_analisis': resultado.get('fecha', ''),
                        'tonalidad_promedio': f"{resultado.get('tonalidad', 0):.2f}",
                        'categoria_maduracion': resultado.get('categoria_maduracion', ''),
                        'rugosidad': f"{resultado.get('rugosidad', 0):.4f}",
                        'defectos_porcentaje': f"{resultado.get('defectos', 0):.2f}",
                        'clasificacion': resultado.get('clasificacion', ''),
                        'vida_util_dias': resultado.get('vida_util_dias', ''),
                        'justificacion': resultado.get('justificacion', '')
                    })
            
            return True
        except Exception as e:
            print(f"❌ Error al exportar CSV: {e}")
            return False
    
    @staticmethod
    def exportar_json(resultados: List[Dict], ruta_salida: str) -> bool:
        """
        Exporta resultados a formato JSON.
        
        Args:
            resultados: Lista de diccionarios con resultados de clasificación
            ruta_salida: Ruta del archivo JSON de salida
        
        Returns:
            True si la exportación fue exitosa
        """
        try:
            datos_export = {
                'metadata': {
                    'sistema': 'Clasificador de Limones',
                    'version': '2.0',
                    'fecha_exportacion': datetime.now().isoformat(),
                    'total_muestras': len(resultados)
                },
                'resultados': resultados
            }
            
            with open(ruta_salida, 'w', encoding='utf-8') as f:
                json.dump(datos_export, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"❌ Error al exportar JSON: {e}")
            return False
    
    @staticmethod
    def resultado_a_dict(clasificador, ruta_imagen: str = None) -> Dict:
        """
        Convierte resultado de clasificador a diccionario exportable.
        
        Args:
            clasificador: Instancia de ClasificadorLimones con resultados
            ruta_imagen: Ruta de la imagen analizada
        
        Returns:
            Diccionario con datos estructurados
        """
        vector = clasificador.vector_caracteristicas
        clasificacion = clasificador.clasificacion
        
        return {
            'archivo': Path(ruta_imagen).name if ruta_imagen else 'imagen_memoria',
            'fecha': datetime.now().isoformat(),
            'vector_caracteristicas': {
                'tonalidad': float(vector[0]),
                'rugosidad': float(vector[1]),
                'defectos': float(vector[2])
            },
            'tonalidad': float(vector[0]),
            'rugosidad': float(vector[1]),
            'defectos': float(vector[2]),
            'categoria_maduracion': clasificador.categoria_maduracion,
            'clasificacion': clasificacion['categoria'],
            'vida_util_dias': int(clasificacion['vida_util'].split()[0]),
            'vida_util': clasificacion['vida_util'],
            'justificacion': clasificacion['justificacion'],
            'cumple_exportacion': clasificacion.get('cumple_exportacion', False)
        }


# Ejemplo de uso
if __name__ == "__main__":
    # Datos de ejemplo
    resultados_ejemplo = [
        {
            'archivo': 'limon1.jpg',
            'fecha': '2026-02-16T23:00:00',
            'tonalidad': 27.34,
            'rugosidad': 70.39,
            'defectos': 0.60,
            'categoria_maduracion': 'Pintón',
            'clasificacion': 'CONSUMO LOCAL',
            'vida_util_dias': 7,
            'justificacion': 'Alta rugosidad (70.40)'
        }
    ]
    
    # Exportar a CSV
    DataExporter.exportar_csv(resultados_ejemplo, 'resultados.csv')
    print("✓ Exportado a CSV")
    
    # Exportar a JSON
    DataExporter.exportar_json(resultados_ejemplo, 'resultados.json')
    print("✓ Exportado a JSON")
