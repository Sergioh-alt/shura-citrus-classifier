"""
Modo Industrial en Tiempo Real
Vista principal para operación continua con banda transportadora
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
from queue import Queue
from collections import defaultdict, deque
from datetime import datetime, timedelta
import time
import numpy as np

# Imports del sistema
import sys
sys.path.insert(0, '.')

from camera.camera_capture import CameraCapture
from core.clasificador import ClasificadorLimones
from core.config_manager import ConfigManager
from core.grupos_manager import GruposManager
from hardware.hardware_controller import HardwareController
from database.dao import LimonDAO, AlertaDAO
from utils.alert_system import AlertSystem


class ModoIndustrial:
    """
    Modo de operación industrial con procesamiento continuo.
    """
    
    def __init__(self, parent=None):
        """
        Args:
            parent: Ventana padre (opcional)
        """
        # Configuración de ventana
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("Sistema Industrial - Clasificación en Tiempo Real")
        self.root.geometry("1280x800")
        
        # Estado
        self.running = False
        self.paused = False
        self.total_procesados = 0
        self.inicio_sesion = None
        
        # Componentes del sistema
        self.config = ConfigManager()
        self.grupos_manager = GruposManager()
        self.limon_dao = LimonDAO()
        self.alert_system = AlertSystem()
        
        # Cámara y hardware
        self.camera = None
        self.hardware = None
        self.clasificador = None
        
        # Estadísticas
        self.contadores = defaultdict(int)
        self.historico_fps = deque(maxlen=60)  # Último minuto
        self.historico_throughput = deque(maxlen=60)
        
        # Threading
        self.process_thread = None
        self.frame_actual = None
        self.resultado_actual = None
        
        # UI
        self.crear_interfaz()
        
        # Configurar alerts
        self.alert_system.agregar_callback('warning', self.mostrar_alerta)
        self.alert_system.agregar_callback('error', self.mostrar_alerta)
        self.alert_system.agregar_callback('critical', self.mostrar_alerta)
    
    def crear_interfaz(self):
        """Crear interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame superior: Header
        self.crear_header(main_frame)
        
        # Frame central: dividido en 2 columnas
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Columna izquierda: Cámara
        left_frame = ttk.LabelFrame(center_frame, text="Cámara en Vivo", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.crear_panel_camara(left_frame)
        
        # Columna derecha: Control y Estadísticas
        right_frame = ttk.Frame(center_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        self.crear_panel_control(right_frame)
        self.crear_panel_estadisticas(right_frame)
        
        # Frame inferior: Gráficos
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.crear_panel_graficos(bottom_frame)
    
    def crear_header(self, parent):
        """Crear header con título y estado"""
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 5))
        
        # Título
        ttk.Label(header, text="🍋 Sistema Industrial v3.0", 
                 font=('Segoe UI', 16, 'bold')).pack(side=tk.LEFT)
        
        # Estado
        self.label_estado = ttk.Label(header, text="⏸️ DETENIDO", 
                                      font=('Segoe UI', 12, 'bold'),
                                      foreground='red')
        self.label_estado.pack(side=tk.RIGHT, padx=10)
    
    def crear_panel_camara(self, parent):
        """Panel de visualización de cámara"""
        # Canvas para video
        self.canvas_video = tk.Canvas(parent, width=640, height=480, bg='black')
        self.canvas_video.pack(fill=tk.BOTH, expand=True)
        
        # Info overlay
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.label_fps = ttk.Label(info_frame, text="FPS: --", font=('Consolas', 10))
        self.label_fps.pack(side=tk.LEFT, padx=5)
        
        self.label_contador = ttk.Label(info_frame, text="#0000", font=('Consolas', 10, 'bold'))
        self.label_contador.pack(side=tk.LEFT, padx=20)
        
        self.label_resultado = ttk.Label(info_frame, text="", font=('Consolas', 10))
        self.label_resultado.pack(side=tk.LEFT, padx=5)
    
    def crear_panel_control(self, parent):
        """Panel de control START/STOP"""
        control_frame = ttk.LabelFrame(parent, text="Control de Operación", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Botones grandes
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)
        
        self.btn_start = tk.Button(btn_frame, text="▶️  INICIAR", 
                                   command=self.iniciar_procesamiento,
                                   font=('Segoe UI', 12, 'bold'),
                                   bg='#4CAF50', fg='white',
                                   height=2, width=15)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = tk.Button(btn_frame, text="⏹  DETENER", 
                                  command=self.detener_procesamiento,
                                  font=('Segoe UI', 12, 'bold'),
                                  bg='#f44336', fg='white',
                                  height=2, width=15,
                                  state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        # Configuración rápida
        config_frame = ttk.Frame(control_frame)
        config_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(config_frame, text="Modo Cámara:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.combo_camara = ttk.Combobox(config_frame, values=['Simulado', 'USB', 'IP'], 
                                         state='readonly', width=12)
        self.combo_camara.set('Simulado')
        self.combo_camara.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(config_frame, text="Modo Hardware:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.combo_hardware = ttk.Combobox(config_frame, values=['Simulado', 'Arduino', 'PLC'], 
                                           state='readonly', width=12)
        self.combo_hardware.set('Simulado')
        self.combo_hardware.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
    
    def crear_panel_estadisticas(self, parent):
        """Panel de estadísticas en tiempo real"""
        stats_frame = ttk.LabelFrame(parent, text="Estadísticas en Tiempo Real", padding="10")
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        #  Treeview para contadores por grupo
        self.tree_stats = ttk.Treeview(stats_frame, columns=('total', 'porcentaje'), 
                                      show='tree headings', height=8)
        
        self.tree_stats.heading('#0', text='Grupo')
        self.tree_stats.heading('total', text='Total')
        self.tree_stats.heading('porcentaje', text='%')
        
        self.tree_stats.column('#0', width=150)
        self.tree_stats.column('total', width=60, anchor='center')
        self.tree_stats.column('porcentaje', width=60, anchor='center')
        
        self.tree_stats.pack(fill=tk.BOTH, expand=True)
        
        # Resumen
        resumen_frame = ttk.Frame(stats_frame)
        resumen_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.label_total = ttk.Label(resumen_frame, text="Total: 0", font=('Consolas', 10, 'bold'))
        self.label_total.pack(anchor=tk.W)
        
        self.label_throughput = ttk.Label(resumen_frame, text="Throughput: 0 limones/min")
        self.label_throughput.pack(anchor=tk.W, pady=2)
        
        self.label_tiempo = ttk.Label(resumen_frame, text="Tiempo: 00:00:00")
        self.label_tiempo.pack(anchor=tk.W)
    
    def crear_panel_graficos(self, parent):
        """Panel de gráficos (placeholder)"""
        graficos_frame = ttk.LabelFrame(parent, text="Throughput (último minuto)", padding="10")
        graficos_frame.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder para gráfico
        self.canvas_grafico = tk.Canvas(graficos_frame, height=120, bg='white')
        self.canvas_grafico.pack(fill=tk.BOTH, expand=True)
    
    def iniciar_procesamiento(self):
        """Iniciar procesamiento continuo"""
        if self.running:
            return
        
        # Inicializar componentes
        try:
            # Cámara
            modo_camara = self.combo_camara.get().lower()
            if modo_camara == 'simulado':
                # Modo simulado: usar imagen estática
                self.camera = None
            elif modo_camara == 'usb':
                self.camera = CameraCapture(modo="usb", config={'device_id': 0})
                if not self.camera.iniciar():
                    raise Exception("No se pudo iniciar cámara USB")
            
            # Hardware
            modo_hardware = self.combo_hardware.get().lower()
            self.hardware = HardwareController(modo=modo_hardware)
            if not self.hardware.conectar():
                self.alert_system.registrar_alerta('hardware_desconectado')
            
            # Clasificador
            self.clasificador = ClasificadorLimones(config_manager=self.config, verbose=False)
            
            # Estado
            self.running = True
            self.paused = False
            self.total_procesados = 0
            self.inicio_sesion = datetime.now()
            self.contadores.clear()
            
            # UI
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.label_estado.config(text="▶️ PROCESANDO", foreground='green')
            
            # Thread de procesamiento
            self.process_thread = threading.Thread(target=self.loop_procesamiento, daemon=True)
            self.process_thread.start()
            
            # Thread de actualización UI
            self.actualizar_ui()
            
            messagebox.showinfo("Iniciado", "Sistema industrial iniciado correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el sistema:\n{e}")
            self.detener_procesamiento()
    
    def detener_procesamiento(self):
        """Detener procesamiento"""
        self.running = False
        
        if self.camera:
            self.camera.detener()
        
        if self.hardware:
            self.hardware.desconectar()
        
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.label_estado.config(text="⏹ DETENIDO", foreground='red')
    
    def loop_procesamiento(self):
        """Loop principal de procesamiento"""
        while self.running:
            try:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # Obtener frame
                if self.camera:
                    frame = self.camera.obtener_frame(timeout=1.0)
                    if frame is None:
                        self.alert_system.registrar_alerta('camara_sin_señal')
                        time.sleep(1)
                        continue
                else:
                    # Modo simulado: usar imagen estática
                    frame = cv2.imread('limon_prueba.jpg')
                    time.sleep(2)  # Simular tiempo de captura
                
                self.frame_actual = frame
                
                # Clasificar
                self.clasificador.cargar_desde_array(frame)
                resultado = self.clasificador.procesar(mostrar_visualizacion=False)
                
                if resultado:
                    # Evaluar grupos
                    vector = resultado['vector_caracteristicas']
                    acidez = resultado['acidez_estimada']
                    grupos_cumplidos = self.grupos_manager.clasificar_multi_grupo(vector, acidez)
                    grupo_final = self.grupos_manager.obtener_grupo_prioritario(grupos_cumplidos)
                    salida = self.grupos_manager.obtener_salida_fisica(grupo_final)
                    
                    # Activar hardware
                    if self.hardware:
                        self.hardware.activar_salida(salida, duracion_ms=300)
                    
                    # Guardar en BD
                    self.limon_dao.guardar(
                        tonalidad=vector[0],
                        rugosidad=vector[1],
                        defectos=vector[2],
                        acidez=acidez,
                        grupo_asignado=grupo_final,
                        salida_fisica=salida,
                        modo='industrial_auto'
                    )
                    
                    # Actualizar estadísticas
                    self.total_procesados += 1
                    self.contadores[grupo_final] += 1
                    self.resultado_actual = {
                        'grupo': grupo_final,
                        'acidez': acidez,
                        'salida': salida
                    }
                    
            except Exception as e:
                print(f"Error en procesamiento: {e}")
                self.alert_system.registrar_alerta('error_clasificacion', str(e))
                time.sleep(1)
    
    def actualizar_ui(self):
        """Actualizar interfaz periódicamente"""
        if not self.running:
            return
        
        # Actualizar contador
        self.label_contador.config(text=f"#{self.total_procesados:04d}")
        
        # Actualizar resultado actual
        if self.resultado_actual:
            texto = f"Grupo: {self.resultado_actual['grupo']} | Acidez: {self.resultado_actual['acidez']:.1f}% | Sal ida: {self.resultado_actual['salida']}"
            self.label_resultado.config(text=texto)
        
        # Actualizar estadísticas por grupo
        self.tree_stats.delete(*self.tree_stats.get_children())
        for grupo, total in sorted(self.contadores.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (total / self.total_procesados * 100) if self.total_procesados > 0 else 0
            self.tree_stats.insert('', 'end', text=grupo, values=(total, f"{porcentaje:.1f}%"))
        
        # Actualizar total y throughput
        self.label_total.config(text=f"Total: {self.total_procesados}")
        
        if self.inicio_sesion:
            tiempo_transcurrido = (datetime.now() - self.inicio_sesion).total_seconds()
            if tiempo_transcurrido > 0:
                throughput = (self.total_procesados / tiempo_transcurrido) * 60
                self.label_throughput.config(text=f"Throughput: {throughput:.1f} limones/min")
                
                # Tiempo
                horas = int(tiempo_transcurrido // 3600)
                minutos = int((tiempo_transcurrido % 3600) // 60)
                segundos = int(tiempo_transcurrido % 60)
                self.label_tiempo.config(text=f"Tiempo: {horas:02d}:{minutos:02d}:{segundos:02d}")
        
        # Actualizar frame de video
        if self.frame_actual is not None:
            self.mostrar_frame(self.frame_actual)
        
        # Repetir cada 500ms
        self.root.after(500, self.actualizar_ui)
    
    def mostrar_frame(self, frame):
        """Mostrar frame en canvas"""
        # Redimensionar para canvas
        height, width = frame.shape[:2]
        canvas_width = self.canvas_video.winfo_width()
        canvas_height = self.canvas_video.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Calcular escala manteniendo aspecto
            scale = min(canvas_width / width, canvas_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            frame_resized = cv2.resize(frame, (new_width, new_height))
            
            # Convertir BGR a RGB
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Convertir a PhotoImage
            img = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(image=img)
            
            # Mostrar en canvas
            self.canvas_video.create_image(canvas_width//2, canvas_height//2, image=photo)
            self.canvas_video.image = photo  # Mantener referencia
    
    def mostrar_alerta(self, alerta: dict):
        """Mostrar alerta en popup"""
        simbolos = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }
        
        simbolo = simbolos.get(alerta['severidad'], '•')
        mensaje = f"{simbolo} {alerta['mensaje']}"
        
        if alerta['severidad'] == 'critical':
            messagebox.showerror("Alerta Crítica", mensaje)
        elif alerta['severidad'] == 'error':
            messagebox.showerror("Error", mensaje)
        else:
            messagebox.showwarning("Atención", mensaje)
    
    def run(self):
        """Ejecutar aplicación"""
        self.root.mainloop()


# Ejecutar modo industrial
if __name__ == "__main__":
    app = ModoIndustrial()
    app.run()
