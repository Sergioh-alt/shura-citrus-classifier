"""
Test completo del sistema industrial
Prueba los módulos de acidez, grupos y hardware
"""

import sys
import numpy as np
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from core.clasificador import ClasificadorLimones
from core.config_manager import ConfigManager
from core.grupos_manager import GruposManager
from hardware.hardware_controller import HardwareController


def test_acidez_y_grupos():
    """Test de acidez y sistema de grupos"""
    print("="*70)
    print(" TEST: ACIDEZ Y GRUPOS PERSONALIZADOS")
    print("="*70)
    
    # Cargar configuración
    config = ConfigManager()
    clasificador = ClasificadorLimones("limon_prueba.jpg", config_manager=config, verbose=True)
    
    # Procesar imagen
    resultado = clasificador.procesar(mostrar_visualizacion=False)
    
    if resultado:
        print(f"\n{'='*70}")
        print(f" RESULTADOS:")
        print(f"{'='*70}")
        
        vector = resultado['vector_caracteristicas']
        acidez = resultado['acidez_estimada']
        clasificacion = resultado['clasificacion']
        
        print(f"  Tonalidad: {vector[0]:.2f}°")
        print(f"  Rugosidad: {vector[1]:.2f}")
        print(f"  Defectos: {vector[2]:.2f}%")
        print(f"  🧪 Acidez: {acidez:.2f}%")
        print(f"  Clasificación original: {clasificacion['categoria']}")
        
        # Test de grupos
        print(f"\n{'='*70}")
        print(f" EVALUACIÓN DE GRUPOS:")
        print(f"{'='*70}")
        
        grupos_manager = GruposManager()
        grupos_cumplidos = grupos_manager.clasificar_multi_grupo(
            vector, acidez, vida_util_dias=7
        )
        
        print(f"  Grupos que cumple: {grupos_cumplidos}")
        
        grupo_final = grupos_manager.obtener_grupo_prioritario(grupos_cumplidos)
        salida_fisica = grupos_manager.obtener_salida_fisica(grupo_final)
        
        print(f"  ✓ Grupo final: {grupo_final}")
        print(f"  ✓ Salida física: {salida_fisica}")
        
        return grupo_final, salida_fisica
    
    return None, None


def test_hardware_simulado(grupo, salida):
    """Test del controlador de hardware en modo simulado"""
    print(f"\n{'='*70}")
    print(f" TEST: CONTROLADOR DE HARDWARE (SIMULADO)")
    print(f"{'='*70}")
    
    controller = HardwareController(modo="simulado")
    
    if controller.conectar():
        print(f"\n  → Activando salida {salida} para grupo '{grupo}'...")
        controller.activar_salida(salida, duracion_ms=500)
        
        # Test de todas las salidas
        print(f"\n  → Test de todas las salidas...")
        for i in range(1, 6):
            controller.activar_salida(i, duracion_ms=300)
        
        # Estadísticas
        stats = controller.obtener_estadisticas()
        print(f"\n  📊 Estadísticas:")
        print(f"     Total: {stats['total_activaciones']} activaciones")
        print(f"     Por salida: {stats['activaciones_por_salida']}")
        
        controller.desconectar()
        return True
    
    return False


def test_integracion_completa():
    """Test de integración completa del flujo"""
    print("\n" + "="*70)
    print(" TEST INTEGRACIÓN COMPLETA: IMAGEN → GRUPOS → HARDWARE")
    print("="*70)
    
    # 1. Clasificar imagen
    print("\n[1/3] Clasificando imagen...")
    config = ConfigManager()
    clasificador = ClasificadorLimones("limon_prueba.jpg", config_manager=config, verbose=False)
    resultado = clasificador.procesar(mostrar_visualizacion=False)
    
    if not resultado:
        print("❌ Error al procesar imagen")
        return False
    
    vector = resultado['vector_caracteristicas']
    acidez = resultado['acidez_estimada']
    
    print(f"  ✓ Procesado: H={vector[0]:.1f}°, Acidez={acidez:.1f}%")
    
    # 2. Evaluar grupos
    print("\n[2/3] Evaluando grupos...")
    grupos_manager = GruposManager()
    grupos_cumplidos = grupos_manager.clasificar_multi_grupo(vector, acidez)
    grupo_final = grupos_manager.obtener_grupo_prioritario(grupos_cumplidos)
    salida = grupos_manager.obtener_salida_fisica(grupo_final)
    
    print(f"  ✓ Grupo asignado: '{grupo_final}' → Salida {salida}")
    
    # 3. Activar hardware
    print("\n[3/3] Activando seleccionadora...")
    controller = HardwareController(modo="simulado")
    
    if controller.conectar():
        controller.activar_salida(salida, duracion_ms=500)
        controller.desconectar()
        print(f"  ✓ Seleccionadora {salida} activada")
    
    print(f"\n{'='*70}")
    print(" ✓ TEST COMPLETO EXITOSO")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    print("\n" + "🍋"*35)
    print("   SISTEMA INDUSTRIAL DE CLASIFICACIÓN DE LIMONES")
    print("   Test de Módulos - Versión 2.0")
    print("🍋"*35 + "\n")
    
    try:
        # Test 1: Acidez y grupos
        grupo, salida = test_acidez_y_grupos()
        
        if grupo and salida:
            # Test 2: Hardware
            test_hardware_simulado(grupo, salida)
            
            # Test 3: Integración
            test_integracion_completa()
        
        print("\n✅ TODOS LOS TESTS COMPLETADOS\n")
        
    except Exception as e:
        print(f"\n❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
