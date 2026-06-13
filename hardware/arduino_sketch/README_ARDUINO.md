# Arduino Setup - Sistema de Clasificación de Limones

## Hardware Requerido

### Componentes
- **Arduino Mega 2560** o **Arduino Uno**
- **Módulo de relés de 8 canales** (5V, opto-aislados)
- **Fuente de alimentación** 12V/2A para relés (separada del Arduino)
- **Cable USB** para programación y comunicación con PC
- **Cables jumper** macho-macho

### Lista de Compras (Estimado)
| Componente | Precio Aproximado |
|------------|-------------------|
| Arduino Mega 2560 | $15 USD |
| Módulo 8 relés 5V | $8 USD |
| Fuente 12V/2A | $7 USD |
| Cables jumper | $3 USD |
| **TOTAL** | **~$33 USD** |

## Diagrama de Conexiones

```
Arduino Mega          Módulo de Relés (8 canales)
============          ===========================

Pin 2  ────────────→  IN1  (Salida 1: Brasil)
Pin 3  ────────────→  IN2  (Salida 2: Europa)
Pin 4  ────────────→  IN3  (Salida 3: Local Premium)
Pin 5  ────────────→  IN4  (Salida 4: Industrial)
Pin 6  ────────────→  IN5  (Salida 5: Descarte)
Pin 7  ────────────→  IN6  (Salida 6: Reserva)

GND    ────────────→  GND
5V     ────────────→  VCC


Módulo de Relés       Seleccionadoras Físicas
===============       =======================

COM1   ─┐
NO1    ─┼───────────→ Seleccionadora 1 (+24V)
NC1    ─┘

COM2   ─┐
NO2    ─┼───────────→ Seleccionadora 2 (+24V)
NC2    ─┘

... (repetir para cada canal)

Fuente 12V externa conectada a JD-VCC y GND del módulo de relés
```

## Instalación del Software

### 1. Instalar Arduino IDE

Descargar de: https://www.arduino.cc/en/software

### 2. Cargar el Sketch

1. Abrir Arduino IDE
2. Abrir el archivo `clasificador_limones.ino`
3. Seleccionar placa: **Tools > Board > Arduino Mega 2560**
4. Seleccionar puerto: **Tools > Port > COM3** (ajustar según tu PC)
5. Click en **Upload** (botón de flecha)

### 3. Verificar Funcionamiento

Abrir **Serial Monitor** (Ctrl+Shift+M):
- Baudrate: **9600**
- Line ending: **Newline**

Deberías ver:
```
ARDUINO_READY
Sistema de Clasificacion de Limones v1.0
Salidas disponibles: 6
READY
```

## Testing del Arduino

### Test Manual (Serial Monitor)

Enviar estos comandos en el Serial Monitor:

```
STATUS          → Verifica estado del sistema
TEST            → Activa secuencialmente todas las salidas
S1D500          → Activa salida 1 por 500ms
S2D1000         → Activa salida 2 por 1 segundo
```

Respuestas esperadas:
```
STATUS:OK
SALIDAS:6

TEST:START
ACTIVADO:S1:PIN2:200ms
DESACTIVADO:S1
...
TEST:COMPLETE

OK:S1D500
ACTIVADO:S1:PIN2:500ms
DESACTIVADO:S1
```

### Test desde Python

```python
from hardware.hardware_controller import HardwareController

# Conectar Arduino
controller = HardwareController(modo="arduino", config={'puerto': 'COM3'})

if controller.conectar():
    # Test de salidas
    for i in range(1, 6):
        print(f"Activando salida {i}...")
        controller.activar_salida(i, duracion_ms=500)
        time.sleep(1)
    
    controller.desconectar()
```

## Protocolo Serial

### Comandos PC → Arduino

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `S<num>D<ms>\n` | Activar salida | `S1D500\n` |
| `STATUS\n` | Solicitar estado | `STATUS\n` |
| `TEST\n` | Test de salidas | `TEST\n` |

### Respuestas Arduino → PC

| Respuesta | Significado |
|-----------|-------------|
| `OK:S1D500` | Comando ejecutado |
| `ERROR:INVALID_PARAMS` | Parámetros inválidos |
| `ACTIVADO:S1:PIN2:500ms` | Info de activación |
| `DESACTIVADO:S1` | Salida desactivada |
| `STATUS:OK` | Sistema funcionando |
| `SALIDAS:6` | Número de salidas |

## Solución de Problemas

### Arduino no detectado
- Verificar cable USB
- Instalar drivers CH340/FTDI según el clon
- Reiniciar Arduino IDE

### Relés no activan
- Verificar alimentación externa (JD-VCC)
- Revisar conexiones GND
- Módulo de relés puede tener lógica inverti da (LOW = ON)
  - En ese caso, cambiar en el código:
    ```cpp
    digitalWrite(pin, LOW);   // Para activar
    digitalWrite(pin, HIGH);  // Para desactivar
    ```

### Error "port busy"
- Cerrar Serial Monitor antes de subir código
- Cerrar aplicación Python que use el puerto
- Reiniciar Arduino

## Notas Importantes

⚠️ **SEGURIDAD**:
- Nunca conectar cargas de alta potencia directamente al Arduino
- Siempre usar fuente externa para los relés
- Aislar eléctricamente las seleccionadoras (usar opto-aisladores)
- Agregar fusibles de protección

⚠️ **LÍMITES**:
- Corriente máxima por pin: 40mA
- Duración máxima de pulso: 5000ms (configurable)
- No activar todas las salidas simultáneamente (consumo excesivo)

## Mejoras Futuras

- [ ] Agregar sensor de presencia de limón (trigger externo)
- [ ] LCD para mostrar estadísticas
- [ ] Botón de parada de emergencia
- [ ] Comunicación Ethernet (Arduino Ethernet Shield)
- [ ] Watchdog timer para reinicio automático
