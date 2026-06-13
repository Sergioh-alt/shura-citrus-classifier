"""
Sistema de Alertas para monitoreo en tiempo real
Detecta y notifica problemas del sistema
"""

from database.dao import AlertaDAO
from typing import Dict, List, Callable
from datetime import datetime
import threading
import time


class AlertSystem:
    """
    Sistema de alertas con reglas configurables y múltiples canales de notificación.
    """
    
    # Definición de tipos de alertas
    TIPOS_ALERTAS = {
        'hardware_desconectado': {
            'severidad': 'critical',
            'mensaje': 'Hardware no responde',
            'categoria': 'hardware'
        },
        'camara_sin_señal': {
            'severidad': 'critical',
            'mensaje': 'Cámara desconectada o sin señal',
            'categoria': 'camara'
        },
        'fps_bajo': {
            'severidad': 'warning',
            'mensaje': 'FPS de cámara por debajo del umbral',
            'categoria': 'camara'
        },
        'descarte_alto': {
            'severidad': 'warning',
            'mensaje': 'Porcentaje de descarte elevado',
            'categoria': 'calidad'
        },
        'salida_no_responde': {
            'severidad': 'error',
            'mensaje': 'Salida física no respondió',
            'categoria': 'hardware'
        },
        'db_llena': {
            'severidad': 'warning',
            'mensaje': 'Base de datos alcanzó capacidad crítica',
            'categoria': 'sistema'
        },
        'error_clasificacion': {
            'severidad': 'error',
            'mensaje': 'Error en el proceso de clasificación',
            'categoria': 'sistema'
        },
        'calibracion_requerida': {
            'severidad': 'info',
            'mensaje': 'Se recomienda recalibración del sistema',
            'categoria': 'calidad'
        }
    }
    
    def __init__(self, db_path='database/clasificacion.db'):
        """
        Args:
            db_path: Ruta a la base de datos
        """
        self.db_path = db_path
        self.alerta_dao = AlertaDAO(db_path)
        
        # Callbacks para notificaciones
        self.callbacks: Dict[str, List[Callable]] = {
            'info': [],
            'warning': [],
            'error': [],
            'critical': []
        }
        
        # Configuración de umbrales
        self.umbrales = {
            'fps_minimo': 15,
            'descarte_maximo': 20.0,  # porcentaje
            'tiempo_respuesta_hardware': 5.0,  # segundos
            'db_tamaño_max_mb': 1000
        }
        
        # Estado del sistema
        self.alertas_activas = set()
        self.ultima_verificacion = {}
    
    def registrar_alerta(self, tipo: str, detalles: str = None) -> int:
        """
        Registrar una nueva alerta.
        
        Args:
            tipo: Tipo de alerta (debe estar en TIPOS_ALERTAS)
            detalles: Información adicional
        
        Returns:
            ID de la alerta creada
        """
        if tipo not in self.TIPOS_ALERTAS:
            raise ValueError(f"Tipo de alerta no válido: {tipo}")
        
        config = self.TIPOS_ALERTAS[tipo]
        
        # Crear en BD
        alerta_id = self.alerta_dao.crear(
            tipo=config['categoria'],
            severidad=config['severidad'],
            mensaje=config['mensaje'],
            detalles=detalles
        )
        
        # Agregar a activas
        self.alertas_activas.add(alerta_id)
        
        # Ejecutar callbacks
        self._ejecutar_callbacks(config['severidad'], {
            'id': alerta_id,
            'tipo': tipo,
            'severidad': config['severidad'],
            'mensaje': config['mensaje'],
            'detalles': detalles,
            'timestamp': datetime.now()
        })
        
        return alerta_id
    
    def resolver_alerta(self, alerta_id: int, nota: str = None):
        """Marcar alerta como resuelta"""
        self.alerta_dao.resolver(alerta_id, nota)
        
        if alerta_id in self.alertas_activas:
            self.alertas_activas.remove(alerta_id)
    
    def obtener_alertas_activas(self, severidad: str = None) -> List[Dict]:
        """Obtener alertas no resueltas"""
        return self.alerta_dao.obtener_activas(severidad)
    
    def agregar_callback(self, severidad: str, callback: Callable):
        """
        Agregar función callback para una severidad.
        
        Args:
            severidad: 'info', 'warning', 'error', 'critical'
            callback: Función que recibe dict con datos de alerta
        """
        if severidad not in self.callbacks:
            raise ValueError(f"Severidad no válida: {severidad}")
        
        self.callbacks[severidad].append(callback)
    
    def _ejecutar_callbacks(self, severidad: str, alerta_data: Dict):
        """Ejecutar callbacks registrados"""
        # Callback para esta severidad específica
        for callback in self.callbacks.get(severidad, []):
            try:
                callback(alerta_data)
            except Exception as e:
                print(f"Error en callback: {e}")
        
        # Para critical y error, también ejecutar callbacks de warning
        if severidad in ['critical', 'error']:
            for callback in self.callbacks.get('warning', []):
                try:
                    callback(alerta_data)
                except Exception as e:
                    print(f"Error en callback: {e}")
    
    # Métodos de verificación automática
    
    def verificar_fps(self, fps_actual: float):
        """Verificar FPS de cámara"""
        if fps_actual < self.umbrales['fps_minimo']:
            if 'fps_bajo' not in self.ultima_verificacion or \
               (datetime.now() - self.ultima_verificacion['fps_bajo']).seconds > 60:
                self.registrar_alerta('fps_bajo', f"FPS actual: {fps_actual}")
                self.ultima_verificacion['fps_bajo'] = datetime.now()
    
    def verificar_descarte(self, porcentaje: float):
        """Verificar porcentaje de descarte"""
        if porcentaje > self.umbrales['descarte_maximo']:
            if 'descarte_alto' not in self.ultima_verificacion or \
               (datetime.now() - self.ultima_verificacion['descarte_alto']).seconds > 300:
                self.registrar_alerta('descarte_alto', f"Descarte: {porcentaje:.1f}%")
                self.ultima_verificacion['descarte_alto'] = datetime.now()
    
    def verificar_hardware(self, conectado: bool):
        """Verificar estado del hardware"""
        if not conectado:
            self.registrar_alerta('hardware_desconectado')
    
    def verificar_camara(self, señal: bool):
        """Verificar señal de cámara"""
        if not señal:
            self.registrar_alerta('camara_sin_señal')
    
    def configurar_umbral(self, nombre: str, valor):
        """Actualizar un umbral de configuración"""
        if nombre in self.umbrales:
            self.umbrales[nombre] = valor
        else:
            raise ValueError(f"Umbral no válido: {nombre}")


# Callbacks de ejemplo

def callback_consola(alerta: Dict):
    """Imprime alerta en consola"""
    simbolos = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❌',
        'critical': '🚨'
    }
    
    simbolo = simbolos.get(alerta['severidad'], '•')
    print(f"{simbolo} [{alerta['severidad'].upper()}] {alerta['mensaje']}")
    if alerta.get('detalles'):
        print(f"   Detalles: {alerta['detalles']}")


def callback_log_archivo(alerta: Dict):
    """Escribe alerta en archivo de log"""
    import os
    os.makedirs('logs', exist_ok=True)
    
    with open('logs/alertas.log', 'a', encoding='utf-8') as f:
        f.write(f"[{alerta['timestamp']}] {alerta['severidad'].upper()} - {alerta['mensaje']}\n")
        if alerta.get('detalles'):
            f.write(f"  Detalles: {alerta['detalles']}\n")


# Test del sistema de alertas
if __name__ == "__main__":
    print("=== Test de Sistema de Alertas ===\n")
    
    # Crear sistema
    sistema = AlertSystem()
    
    # Registrar callbacks
    print("1. Registrando callbacks...")
    sistema.agregar_callback('warning', callback_consola)
    sistema.agregar_callback('error', callback_consola)
    sistema.agregar_callback('critical', callback_consola)
    sistema.agregar_callback('warning', callback_log_archivo)
    print("   ✓ Callbacks registrados\n")
    
    # Test de alertas
    print("2. Generando alertas de prueba...")
    
    sistema.registrar_alerta('fps_bajo', "FPS: 12.5")
    time.sleep(0.5)
    
    sistema.registrar_alerta('descarte_alto', "Descarte: 25.3%")
    time.sleep(0.5)
    
    sistema.registrar_alerta('hardware_desconectado')
    time.sleep(0.5)
    
    # Obtener alertas activas
    print("\n3. Alertas activas:")
    alertas = sistema.obtener_alertas_activas()
    print(f"   Total: {len(alertas)}")
    
    # Test de verificaciones automáticas
    print("\n4. Test de verificaciones automáticas...")
    sistema.verificar_fps(12.0)  # Debería generar alerta
    sistema.verificar_descarte(25.0)  # Debería generar alerta
    
    # Resolver alerta
    print("\n5. Resolviendo alertas...")
    if alertas:
        primera_id = alertas[0]['id']
        sistema.resolver_alerta(primera_id, "Problema resuelto")
        print(f"   ✓ Alerta {primera_id} resuelta")
    
    # Verificar log
    print("\n6. Verificando log de archivo...")
    if os.path.exists('logs/alertas.log'):
        with open('logs/alertas.log', 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        print(f"   ✓ {len(lineas)} líneas en log")
    
    print("\n✅ Test de sistema de alertas completado")
