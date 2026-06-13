"""
Sistema de Grupos de Clasificación Personalizados
Permite crear grupos con criterios específicos para diferentes destinos de exportación
"""

import json
import os
from typing import Dict, List, Optional
import numpy as np


class GrupoClasificacion:
    """
    Representa un grupo de clasificación con criterios personalizados.
    """
    
    def __init__(self, nombre: str, criterios: Dict, prioridad: int = 999, 
                 salida_fisica: int = 1, descripcion: str = ""):
        """
        Args:
            nombre: Nombre del grupo (ej: "Exportación Brasil")
            criterios: Diccionario con criterios de aceptación
            prioridad: Prioridad del grupo (1 = más alta)
            salida_fisica: Número de salida física (1-N)
            descripcion: Descripción opcional del grupo
        """
        self.nombre = nombre
        self.criterios = criterios
        self.prioridad = prioridad
        self.salida_fisica = salida_fisica
        self.descripcion = descripcion
    
    def evaluar(self, vector_caracteristicas: np.ndarray, acidez: float, 
                vida_util_dias: int = None) -> bool:
        """
        Evalúa si un limón cumple los criterios del grupo.
        
        Args:
            vector_caracteristicas: [H, rugosidad, defectos]
            acidez: Porcentaje de acidez estimada
            vida_util_dias: Vida útil estimada en días
        
        Returns:
            True si cumple todos los criterios
        """
        H, rugosidad, defectos = vector_caracteristicas
        
        # Evaluar cada criterio del grupo
        criterios_checks = []
        
        # Acidez
        if 'acidez_min' in self.criterios:
            criterios_checks.append(acidez >= self.criterios['acidez_min'])
        if 'acidez_max' in self.criterios:
            criterios_checks.append(acidez <= self.criterios['acidez_max'])
        
        # Tonalidad (H)
        if 'tonalidad_min' in self.criterios:
            criterios_checks.append(H >= self.criterios['tonalidad_min'])
        if 'tonalidad_max' in self.criterios:
            criterios_checks.append(H <= self.criterios['tonalidad_max'])
        
        # Rugosidad
        if 'rugosidad_max' in self.criterios:
            criterios_checks.append(rugosidad <= self.criterios['rugosidad_max'])
        
        # Defectos
        if 'defectos_max' in self.criterios:
            criterios_checks.append(defectos <= self.criterios['defectos_max'])
        
        # Vida útil
        if 'vida_util_min' in self.criterios and vida_util_dias is not None:
            criterios_checks.append(vida_util_dias >= self.criterios['vida_util_min'])
        
        # Debe cumplir TODOS los criterios
        return all(criterios_checks) if criterios_checks else False
    
    def to_dict(self) -> Dict:
        """Convierte el grupo a diccionario para serialización"""
        return {
            'nombre': self.nombre,
            'prioridad': self.prioridad,
            'salida_fisica': self.salida_fisica,
            'descripcion': self.descripcion,
            'criterios': self.criterios
        }


class GruposManager:
    """
    Gestor de grupos de clasificación personalizados.
    """
    
    def __init__(self, archivo_grupos: str = "grupos.json"):
        """
        Args:
            archivo_grupos: Ruta al archivo JSON de configuración de grupos
        """
        self.archivo_grupos = archivo_grupos
        self.grupos: List[GrupoClasificacion] = []
        self.cargar_grupos()
    
    def cargar_grupos(self) -> bool:
        """
        Carga grupos desde archivo JSON.
        
        Returns:
            True si se cargaron exitosamente
        """
        try:
            if os.path.exists(self.archivo_grupos):
                with open(self.archivo_grupos, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.grupos = []
                for g in data['grupos']:
                    self.grupos.append(GrupoClasificacion(
                        nombre=g['nombre'],
                        criterios=g['criterios'],
                        prioridad=g.get('prioridad', 999),
                        salida_fisica=g.get('salida_fisica', 1),
                        descripcion=g.get('descripcion', '')
                    ))
                
                print(f"✓ Cargados {len(self.grupos)} grupos de clasificación")
                return True
            else:
                print(f"[WARN] Archivo {self.archivo_grupos} no encontrado")
                self.crear_grupos_default()
                return True
        except Exception as e:
            print(f"[ERR] Error al cargar grupos: {e}")
            self.crear_grupos_default()
            return False
    
    def crear_grupos_default(self):
        """Crea grupos de ejemplo por defecto"""
        self.grupos = [
            GrupoClasificacion(
                nombre="Exportación Brasil",
                prioridad=1,
                salida_fisica=1,
                criterios={
                    'acidez_min': 5.0,
                    'acidez_max': 7.0,
                    'tonalidad_min': 25,
                    'tonalidad_max': 40,
                    'rugosidad_max': 45.0,
                    'defectos_max': 3.0,
                    'vida_util_min': 23
                },
                descripcion="Limones pintones con alta acidez para mercado brasileño"
            ),
            GrupoClasificacion(
                nombre="Exportación Europa",
                prioridad=2,
                salida_fisica=2,
                criterios={
                    'acidez_min': 3.0,
                    'acidez_max': 5.0,
                    'tonalidad_min': 30,
                    'tonalidad_max': 50,
                    'rugosidad_max': 35.0,
                    'defectos_max': 2.0,
                    'vida_util_min': 30
                },
                descripcion="Limones premium para mercado europeo"
            ),
            GrupoClasificacion(
                nombre="Mercado Local Premium",
                prioridad=3,
                salida_fisica=3,
                criterios={
                    'acidez_min': 2.5,
                    'acidez_max': 6.0,
                    'rugosidad_max': 50.0,
                    'defectos_max': 5.0
                },
                descripcion="Mercado local de alta calidad"
            ),
            GrupoClasificacion(
                nombre="Procesamiento Industrial",
                prioridad=4,
                salida_fisica=4,
                criterios={
                    'acidez_min': 4.0,
                    'defectos_max': 15.0
                },
                descripcion="Para jugos y procesados"
            ),
            GrupoClasificacion(
                nombre="Descarte",
                prioridad=999,
                salida_fisica=5,
                criterios={},
                descripcion="No cumple ningún criterio de calidad"
            )
        ]
        
        self.guardar_grupos()
        print("✓ Grupos por defecto creados")
    
    def guardar_grupos(self) -> bool:
        """
        Guarda los grupos actuales al archivo JSON.
        
        Returns:
            True si se guardaron exitosamente
        """
        try:
            data = {
                'version': '1.0',
                'grupos': [g.to_dict() for g in self.grupos]
            }
            
            with open(self.archivo_grupos, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Grupos guardados en {self.archivo_grupos}")
            return True
        except Exception as e:
            print(f"❌ Error al guardar grupos: {e}")
            return False
    
    def clasificar_multi_grupo(self, vector_caracteristicas: np.ndarray, 
                              acidez: float, vida_util_dias: int = None) -> List[str]:
        """
        Evalúa un limón contra todos los grupos.
        
        Args:
            vector_caracteristicas: [H, rugosidad, defectos]
            acidez: Porcentaje de acidez
            vida_util_dias: Vida útil estimada
        
        Returns:
            Lista de nombres de grupos que cumplen
        """
        grupos_cumplidos = []
        
        for grupo in self.grupos:
            if grupo.nombre == "Descarte":
                continue  # El descarte se asigna al final si no cumple ninguno
            
            if grupo.evaluar(vector_caracteristicas, acidez, vida_util_dias):
                grupos_cumplidos.append(grupo.nombre)
        
        return grupos_cumplidos
    
    def obtener_grupo_prioritario(self, grupos_cumplidos: List[str]) -> str:
        """
        Retorna el grupo de mayor prioridad de una lista.
        
        Args:
            grupos_cumplidos: Lista de nombres de grupos
        
        Returns:
            Nombre del grupo con mayor prioridad (menor número)
        """
        if not grupos_cumplidos:
            return "Descarte"
        
        # Buscar el grupo con menor número de prioridad (más alta)
        grupo_prioritario = None
        min_prioridad = float('inf')
        
        for grupo in self.grupos:
            if grupo.nombre in grupos_cumplidos and grupo.prioridad < min_prioridad:
                min_prioridad = grupo.prioridad
                grupo_prioritario = grupo.nombre
        
        return grupo_prioritario if grupo_prioritario else grupos_cumplidos[0]
    
    def obtener_salida_fisica(self, nombre_grupo: str) -> int:
        """
        Obtiene el número de salida física para un grupo.
        
        Args:
            nombre_grupo: Nombre del grupo
        
        Returns:
            Número de salida física (1-N)
        """
        for grupo in self.grupos:
            if grupo.nombre == nombre_grupo:
                return grupo.salida_fisica
        return 1  # Default
    
    def agregar_grupo(self, nombre: str, criterios: Dict, prioridad: int = 999,
                     salida_fisica: int = 1, descripcion: str = "") -> bool:
        """Agrega un nuevo grupo"""
        if any(g.nombre == nombre for g in self.grupos):
            print(f"[WARN] Ya existe un grupo con el nombre '{nombre}'")
            return False
        
        nuevo_grupo = GrupoClasificacion(nombre, criterios, prioridad, 
                                        salida_fisica, descripcion)
        self.grupos.append(nuevo_grupo)
        self.guardar_grupos()
        return True
    
    def eliminar_grupo(self, nombre: str) -> bool:
        """Elimina un grupo por nombre"""
        self.grupos = [g for g in self.grupos if g.nombre != nombre]
        self.guardar_grupos()
        return True
    
    def obtener_grupo(self, nombre: str) -> Optional[GrupoClasificacion]:
        """Obtiene un grupo por nombre"""
        for grupo in self.grupos:
            if grupo.nombre == nombre:
                return grupo
        return None


# Ejemplo de uso
if __name__ == "__main__":
    manager = GruposManager()
    
    # Simular clasificación
    vector_test = np.array([27.34, 45.0, 2.5])  # H, rugosidad, defectos
    acidez_test = 6.2
    vida_util_test = 25
    
    grupos_cumplidos = manager.clasificar_multi_grupo(vector_test, acidez_test, vida_util_test)
    print(f"\nGrupos cumplidos: {grupos_cumplidos}")
    
    grupo_final = manager.obtener_grupo_prioritario(grupos_cumplidos)
    salida = manager.obtener_salida_fisica(grupo_final)
    print(f"Grupo final: {grupo_final} → Salida física: {salida}")
