"""
Controlador de Hardware para Seleccionadoras Físicas
Soporta: Arduino (Serial), PLC (Modbus TCP/RTU), Raspberry Pi (GPIO), Simulado
"""

import time
from typing import Dict, Optional
import threading


class HardwareController:
    """
    Controlador universal para activar seleccionadoras físicas en banda transportadora.
    """
    
    def __init__(self, modo: str = "simulado", config: Dict = None):
        """
        Args:
            modo: 'arduino', 'modbus_tcp', 'modbus_rtu', 'gpio', 'simulado'
            config: Configuración específica del modo
                Arduino: {'puerto': 'COM3', 'baudrate': 9600}
                Modbus TCP: {'ip': '192.168.1.100', 'puerto': 502}
                Modbus RTU: {'puerto': 'COM1', 'baudrate': 9600, 'slave_id': 1}
                GPIO: {'pines': [17, 18, 27, 22, 23, 24]}
        """
        self.modo = modo
        self.config = config or {}
        self.conexion = None
        self.conectado = False
        
        # Estadísticas
        self.total_activaciones = 0
        self.activaciones_por_salida = {}
    
    def conectar(self) -> bool:
        """
        Establece conexión con el hardware.
        
        Returns:
            True si la conexión fue exitosa
        """
        try:
            if self.modo == "arduino":
                return self._conectar_arduino()
            elif self.modo == "modbus_tcp":
                return self._conectar_modbus_tcp()
            elif self.modo == "modbus_rtu":
                return self._conectar_modbus_rtu()
            elif self.modo == "gpio":
                return self._conectar_gpio()
            elif self.modo == "simulado":
                return self._conectar_simulado()
            else:
                print(f"❌ Modo de hardware no soportado: {self.modo}")
                return False
        except Exception as e:
            print(f"❌ Error al conectar hardware: {e}")
            return False
    
    def _conectar_arduino(self) -> bool:
        """Conecta con Arduino vía puerto serial"""
        try:
            import serial
            
            puerto = self.config.get('puerto', 'COM3')
            baudrate = self.config.get('baudrate', 9600)
            
            self.conexion = serial.Serial(puerto, baudrate, timeout=1)
            time.sleep(2)  # Esperar reset de Arduino
            
            print(f"✓ Arduino conectado en {puerto} @ {baudrate} baud")
            self.conectado = True
            return True
        except ImportError:
            print("❌ Librería pyserial no instalada. Ejecute: pip install pyserial")
            return False
        except Exception as e:
            print(f"❌ Error al conectar Arduino: {e}")
            return False
    
    def _conectar_modbus_tcp(self) -> bool:
        """Conecta con PLC vía Modbus TCP"""
        try:
            from pymodbus.client import ModbusTcpClient
            
            ip = self.config.get('ip', '192.168.1.100')
            puerto = self.config.get('puerto', 502)
            
            self.conexion = ModbusTcpClient(ip, port=puerto)
            
            if self.conexion.connect():
                print(f"✓ PLC Modbus TCP conectado: {ip}:{puerto}")
                self.conectado = True
                return True
            else:
                print(f"❌ No se pudo conectar al PLC en {ip}:{puerto}")
                return False
        except ImportError:
            print("❌ Librería pymodbus no instalada. Ejecute: pip install pymodbus")
            return False
        except Exception as e:
            print(f"❌ Error al conectar PLC: {e}")
            return False
    
    def _conectar_modbus_rtu(self) -> bool:
        """Conecta con PLC vía Modbus RTU (serial)"""
        try:
            from pymodbus.client import ModbusSerialClient
            
            puerto = self.config.get('puerto', 'COM1')
            baudrate = self.config.get('baudrate', 9600)
            
            self.conexion = ModbusSerialClient(
                port=puerto,
                baudrate=baudrate,
                timeout=1
            )
            
            if self.conexion.connect():
                print(f"✓ PLC Modbus RTU conectado: {puerto} @ {baudrate} baud")
                self.conectado = True
                return True
            else:
                print(f"❌ No se pudo conectar al PLC en {puerto}")
                return False
        except ImportError:
            print("❌ Librería pymodbus no instalada. Ejecute: pip install pymodbus")
            return False
        except Exception as e:
            print(f"❌ Error al conectar PLC RTU: {e}")
            return False
    
    def _conectar_gpio(self) -> bool:
        """Conecta con GPIO de Raspberry Pi"""
        try:
            import RPi.GPIO as GPIO
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Configurar pines como salida
            pines = self.config.get('pines', [17, 18, 27, 22, 23, 24])
            for pin in pines:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            
            self.conexion = GPIO
            self.gpio_pines = pines
            
            print(f"✓ GPIO configurado: pines {pines}")
            self.conectado = True
            return True
        except ImportError:
            print("❌ Librería RPi.GPIO no instalada (solo disponible en Raspberry Pi)")
            print("   Para testing en PC, use modo 'simulado'")
            return False
        except Exception as e:
            print(f"❌ Error al configurar GPIO: {e}")
            return False
    
    def _conectar_simulado(self) -> bool:
        """Modo simulado para testing sin hardware"""
        print("✓ Modo simulado activo (sin hardware físico)")
        self.conectado = True
        return True
    
    def activar_salida(self, numero_salida: int, duracion_ms: int = 500):
        """
        Activa una salida física por un tiempo determinado.
        
        Args:
            numero_salida: Número de salida (1-N)
            duracion_ms: Duración del pulso en milisegundos
        """
        if not self.conectado:
            print("⚠️  Hardware no conectado")
            return
        
        # Actualizar estadísticas
        self.total_activaciones += 1
        if numero_salida not in self.activaciones_por_salida:
            self.activaciones_por_salida[numero_salida] = 0
        self.activaciones_por_salida[numero_salida] += 1
        
        # Ejecutar activación según modo
        if self.modo == "arduino":
            self._activar_arduino(numero_salida, duracion_ms)
        elif self.modo in ["modbus_tcp", "modbus_rtu"]:
            self._activar_modbus(numero_salida, duracion_ms)
        elif self.modo == "gpio":
            self._activar_gpio(numero_salida, duracion_ms)
        elif self.modo == "simulado":
            self._activar_simulado(numero_salida, duracion_ms)
    
    def _activar_arduino(self, salida: int, duracion_ms: int):
        """Envía comando al Arduino"""
        try:
            # Protocolo: "S<num>D<ms>\n"
            # Ejemplo: "S1D500\n" → Activar salida 1 por 500ms
            comando = f"S{salida}D{duracion_ms}\n"
            self.conexion.write(comando.encode())
            
            print(f"→ Arduino: Salida {salida} activada por {duracion_ms}ms")
            
            # Leer confirmación (si el Arduino la envía)
            time.sleep(0.05)
            if self.conexion.in_waiting > 0:
                respuesta = self.conexion.readline().decode().strip()
                print(f"   Arduino responde: {respuesta}")
        except Exception as e:
            print(f"❌ Error al activar Arduino: {e}")
    
    def _activar_modbus(self, salida: int, duracion_ms: int):
        """Activa coil en PLC Modbus"""
        try:
            address = salida - 1  # Ajustar índice (PLC suele empezar en 0)
            slave_id = self.config.get('slave_id', 1)
            
            # Activar coil
            self.conexion.write_coil(address, True, slave=slave_id)
            print(f"→ PLC: Coil {address} activado")
            
            # Esperar duración
            time.sleep(duracion_ms / 1000.0)
            
            # Desactivar coil
            self.conexion.write_coil(address, False, slave=slave_id)
            print(f"   PLC: Coil {address} desactivado")
        except Exception as e:
            print(f"❌ Error al activar PLC: {e}")
    
    def _activar_gpio(self, salida: int, duracion_ms: int):
        """Activa pin GPIO"""
        try:
            if salida - 1 < len(self.gpio_pines):
                pin = self.gpio_pines[salida - 1]
                
                self.conexion.output(pin, self.conexion.HIGH)
                print(f"→ GPIO: Pin {pin} (salida {salida}) activado")
                
                time.sleep(duracion_ms / 1000.0)
                
                self.conexion.output(pin, self.conexion.LOW)
                print(f"   GPIO: Pin {pin} desactivado")
            else:
                print(f"⚠️  Salida {salida} no tiene pin GPIO asignado")
        except Exception as e:
            print(f"❌ Error al activar GPIO: {e}")
    
    def _activar_simulado(self, salida: int, duracion_ms: int):
        """Simula activación (para testing)"""
        print(f"🔵 [SIMULADO] Salida {salida} → {duracion_ms}ms")
        # Podría agregar logs a archivo o base de datos aquí
    
    def obtener_estadisticas(self) -> Dict:
        """Retorna estadísticas de activaciones"""
        return {
            'total_activaciones': self.total_activaciones,
            'activaciones_por_salida': self.activaciones_por_salida.copy()
        }
    
    def desconectar(self):
        """Cierra la conexión con el hardware"""
        if not self.conectado:
            return
        
        try:
            if self.modo == "arduino":
                if self.conexion:
                    self.conexion.close()
            elif self.modo in ["modbus_tcp", "modbus_rtu"]:
                if self.conexion:
                    self.conexion.close()
            elif self.modo == "gpio":
                if self.conexion:
                    self.conexion.cleanup()
            
            print(f"✓ Hardware desconectado ({self.total_activaciones} activaciones totales)")
            self.conectado = False
        except Exception as e:
            print(f"⚠️  Error al desconectar: {e}")


# Test de hardware
if __name__ == "__main__":
    import sys
    
    print("=== Test de Controlador de Hardware ===")
    print("Seleccione modo:")
    print("1. Arduino (Serial)")
    print("2. Modbus TCP (PLC)")
    print("3. Modbus RTU (PLC Serial)")
    print("4. GPIO (Raspberry Pi)")
    print("5. Simulado (Testing)")
    
    opcion = input("Opción (1-5): ").strip() or "5"
    
    if opcion == "1":
        puerto = input("Puerto (ej: COM3): ").strip() or "COM3"
        controller = HardwareController(modo="arduino", config={'puerto': puerto})
    elif opcion == "2":
        ip = input("IP del PLC: ").strip() or "192.168.1.100"
        controller = HardwareController(modo="modbus_tcp", config={'ip': ip})
    elif opcion == "3":
        puerto = input("Puerto (ej: COM1): ").strip() or "COM1"
        controller = HardwareController(modo="modbus_rtu", config={'puerto': puerto})
    elif opcion == "4":
        controller = HardwareController(modo="gpio")
    elif opcion == "5":
        controller = HardwareController(modo="simulado")
    else:
        print("Opción inválida")
        sys.exit(1)
    
    if controller.conectar():
        print("\n✓ Hardware conectado. Testing...")
        
        try:
            # Test de 5 salidas
            for i in range(1, 6):
                print(f"\nActivando salida {i}...")
                controller.activar_salida(i, duracion_ms=300)
                time.sleep(1)
            
            # Mostrar estadísticas
            stats = controller.obtener_estadisticas()
            print(f"\n📊 Estadísticas:")
            print(f"   Total activaciones: {stats['total_activaciones']}")
            print(f"   Por salida: {stats['activaciones_por_salida']}")
            
        except KeyboardInterrupt:
            print("\n\nInterrumpido por usuario")
        finally:
            controller.desconectar()
    else:
        print("❌ No se pudo conectar al hardware")
