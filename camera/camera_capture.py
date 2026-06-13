"""
Módulo de Captura de Cámara Multi-Protocolo
Soporta: USB, IP, Raspberry Pi Camera
"""

import cv2
import numpy as np
import threading
from queue import Queue
from typing import Optional, Tuple
import time


class CameraCapture:
    """
    Captura continua de imágenes desde cámara.
    Soporta USB, IP y Raspberry Pi Camera.
    """
    
    def __init__(self, modo: str = "usb", config: dict = None):
        """
        Args:
            modo: 'usb', 'ip', 'picamera'
            config: Configuración específica del modo
                USB: {'device_id': 0, 'width': 640, 'height': 480, 'fps': 30}
                IP: {'url': 'http://192.168.1.100:8080/video'}
                PiCamera: {'width': 640, 'height': 480, 'fps': 30}
        """
        self.modo = modo
        self.config = config or {}
        self.cap = None
        self.running = False
        self.frame_queue = Queue(maxsize=10)
        self.thread = None
        
        # Configuración por defecto
        self.width = self.config.get('width', 640)
        self.height = self.config.get('height', 480)
        self.fps = self.config.get('fps', 30)
        
        # Estadísticas
        self.frames_capturados = 0
        self.fps_real = 0.0
    
    def iniciar(self) -> bool:
        """
        Inicia la captura de video.
        
        Returns:
            True si se inició correctamente
        """
        try:
            if self.modo == "usb":
                return self._iniciar_usb()
            elif self.modo == "ip":
                return self._iniciar_ip()
            elif self.modo == "picamera":
                return self._iniciar_picamera()
            else:
                print(f"❌ Modo de cámara no soportado: {self.modo}")
                return False
        except Exception as e:
            print(f"❌ Error al iniciar cámara: {e}")
            return False
    
    def _iniciar_usb(self) -> bool:
        """Inicializa cámara USB"""
        device_id = self.config.get('device_id', 0)
        self.cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)  # DSHOW para Windows
        
        if not self.cap.isOpened():
            print(f"❌ No se pudo abrir cámara USB {device_id}")
            return False
        
        # Configurar resolución y FPS
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Verificar configuración real
        real_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        real_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"✓ Cámara USB iniciada: {real_width}x{real_height} @ {self.fps}fps")
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True
    
    def _iniciar_ip(self) -> bool:
        """Inicializa cámara IP"""
        url = self.config.get('url', '')
        if not url:
            print("❌ URL de cámara IP no especificada")
            return False
        
        self.cap = cv2.VideoCapture(url)
        
        if not self.cap.isOpened():
            print(f"❌ No se pudo conectar a cámara IP: {url}")
            return False
        
        print(f"✓ Cámara IP conectada: {url}")
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True
    
    def _iniciar_picamera(self) -> bool:
        """Inicializa Raspberry Pi Camera"""
        try:
            from picamera2 import Picamera2
            
            self.picam = Picamera2()
            config = self.picam.create_preview_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"}
            )
            self.picam.configure(config)
            self.picam.start()
            
            print(f"✓ Raspberry Pi Camera iniciada: {self.width}x{self.height}")
            
            self.running = True
            self.thread = threading.Thread(target=self._capture_loop_picamera, daemon=True)
            self.thread.start()
            return True
        except ImportError:
            print("❌ Librería picamera2 no instalada (solo disponible en Raspberry Pi)")
            return False
        except Exception as e:
            print(f"❌ Error al iniciar Pi Camera: {e}")
            return False
    
    def _capture_loop(self):
        """Loop de captura para USB e IP"""
        ultimo_tiempo = time.time()
        frames_en_segundo = 0
        
        while self.running:
            ret, frame = self.cap.read()
            
            if ret:
                # Convertir BGR a RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Si la cola está llena, descartar frame más viejo
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                
                self.frame_queue.put(frame_rgb)
                self.frames_capturados += 1
                frames_en_segundo += 1
                
                # Calcular FPS real
                tiempo_actual = time.time()
                if tiempo_actual - ultimo_tiempo >= 1.0:
                    self.fps_real = frames_en_segundo / (tiempo_actual - ultimo_tiempo)
                    frames_en_segundo = 0
                    ultimo_tiempo = tiempo_actual
            else:
                print("⚠️  Frame perdido")
                time.sleep(0.01)
    
    def _capture_loop_picamera(self):
        """Loop de captura para Pi Camera"""
        while self.running:
            frame_rgb = self.picam.capture_array()
            
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except:
                    pass
            
            self.frame_queue.put(frame_rgb)
            self.frames_capturados += 1
    
    def obtener_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Obtiene el frame más reciente.
        
        Args:
            timeout: Tiempo máximo de espera en segundos
        
        Returns:
            Frame RGB como numpy array, o None si timeout
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except:
            return None
    
    def obtener_estadisticas(self) -> dict:
        """Retorna estadísticas de captura"""
        return {
            'frames_capturados': self.frames_capturados,
            'fps_real': self.fps_real,
            'frames_en_cola': self.frame_queue.qsize()
        }
    
    def detener(self):
        """Detiene la captura"""
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
        
        if hasattr(self, 'picam'):
            self.picam.stop()
        
        # Limpiar cola
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except:
                break
        
        print(f"✓ Cámara detenida ({self.frames_capturados} frames capturados)")


# Test de cámara
if __name__ == "__main__":
    import sys
    
    print("=== Test de Cámara ===")
    print("Seleccione modo:")
    print("1. USB (default)")
    print("2. IP")
    print("3. Raspberry Pi Camera")
    
    opcion = input("Opción (1-3): ").strip() or "1"
    
    if opcion == "1":
        camera = CameraCapture(modo="usb", config={'device_id': 0})
    elif opcion == "2":
        url = input("URL de cámara IP: ")
        camera = CameraCapture(modo="ip", config={'url': url})
    elif opcion == "3":
        camera = CameraCapture(modo="picamera")
    else:
        print("Opción inválida")
        sys.exit(1)
    
    if camera.iniciar():
        print("\n✓ Capturando. Presione Ctrl+C para detener...")
        
        try:
            while True:
                frame = camera.obtener_frame(timeout=1.0)
                if frame is not None:
                    # Convertir a BGR para mostrar con OpenCV
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Mostrar estadísticas
                    stats = camera.obtener_estadisticas()
                    cv2.putText(frame_bgr, f"FPS: {stats['fps_real']:.1f}", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow('Camera Test', frame_bgr)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        except KeyboardInterrupt:
            print("\n\nDeteniendo...")
        finally:
            camera.detener()
            cv2.destroyAllWindows()
    else:
        print("❌ No se pudo iniciar la cámara")
