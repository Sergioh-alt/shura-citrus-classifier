# Sistema de Clasificación de Limones para Exportación

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Sistema automatizado de clasificación de limones basado en **Álgebra Lineal** y **Visión por Computadora**. Analiza imágenes digitales como tensores de datos discretos para determinar la calidad y vida útil estimada del fruto.

![Sistema de Clasificación](limon_prueba_resultado.jpg)

## 🎯 Características Principales

### 🔬 Análisis Matemático
- **Tensor de Orden 3**: Procesamiento de imágenes como matrices m×n×3
- **Transformación RGB→HSV**: Cambio de base vectorial para análisis cromático
- **Convolución Matricial**: Operador de Sobel para detección de bordes
- **Vector de Características**: v ∈ ℝ³ [Tonalidad, Rugosidad, Defectos]

### 🖥️ Interfaz Dual
- **Modo GUI**: Interfaz gráfica moderna con tkinter
- **Modo CLI**: Línea de comandos para automatización

### ⚙️ Configuración Dinámica
- Parámetros ajustables en tiempo real
- Archivo JSON editable
- Interfaz visual con sliders

### 📊 Exportación Múltiple
- **CSV**: Datos tabulares para análisis
- **JSON**: Estructura completa con metadata
- **Imágenes**: Visualización de análisis completo

## 🚀 Instalación

### Requisitos
- Python 3.13+ (recomendado 3.13.5)
- pip (gestor de paquetes)

### Dependencias

```bash
# Instalar todas las dependencias
py -m pip install numpy opencv-python matplotlib pillow
```

**Dependencias principales:**
- `numpy`: Cálculo matricial y álgebra lineal
- `opencv-python`: Procesamiento de imágenes y convolución
- `matplotlib`: Visualización de resultados
- `pillow`: Manipulación de imágenes para GUI

## 📖 Uso

### Modo GUI (Interfaz Gráfica)

```bash
# Iniciar aplicación con interfaz gráfica
py app.py
```

**Pasos en la GUI:**
1. Click en "📁 Cargar Imagen" o presione `Ctrl+O`
2. Seleccione imagen de limón
3. Click en "🔍 Clasificar"
4. Revise resultados en tabs de visualización
5. Ajuste parámetros en "⚙️ Configuración" si desea
6. Exporte resultados a CSV/JSON

### Modo CLI (Línea de Comandos)

```bash
# Clasificación básica
py app.py --cli limon.jpg

# Con exportación a JSON
py app.py --cli limon.jpg --export-json resultados.json

# Con exportación a CSV
py app.py --cli limon.jpg --export-csv datos.csv

# Modo silencioso sin visualización
py app.py --cli limon.jpg --no-show --quiet --export-json datos.json

# Con configuración personalizada
py app.py --cli limon.jpg --config mi_config.json
```

**Opciones de CLI:**
- `--cli IMAGEN`: Ejecutar en modo línea de comandos
- `--config ARCHIVO`: Usar configuración personalizada
- `--export-csv ARCHIVO`: Exportar a CSV
- `--export-json ARCHIVO`: Exportar a JSON
- `--no-show`: No mostrar ventana de visualización
- `--quiet, -q`: Modo silencioso sin logs
- `--version`: Mostrar versión

## ⚙️ Configuración

El sistema utiliza un archivo `config.json` para almacenar parámetros ajustables:

```json
{
  "clasificacion": {
    "tonalidad": {
      "verde": {"min": 35, "max": 85},
      "pinton": {"min": 20, "max": 34},
      "amarillo": {"min": 0, "max": 19}
    },
    "rugosidad": {
      "umbral_exportacion": 50.0
    },
    "defectos": {
      "porcentaje_maximo": 5.0,
      "umbral_deteccion": 100.0
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
      "dias": 7
    }
  }
}
```

### Parámetros Editables

| Parámetro | Descripción | Rango Sugerido |
|-----------|-------------|----------------|
| `rugosidad.umbral_exportacion` | Coeficiente máximo de rugosidad para exportación | 10-100 |
| `defectos.porcentaje_maximo` | % máximo de defectos superficiales | 1-20% |
| `tonalidad.*` | Rangos de clasificación de madurez (grados) | 0-180° |

## 🏗️ Arquitectura del Proyecto

```
d:\Shura\
│
├── app.py                      # Punto de entrada principal (CLI/GUI)
├── config.json                 # Configuración de parámetros
│
├── core/                       # Módulo de clasificación
│   ├── __init__.py
│   ├── clasificador.py         # Clase principal del clasificador
│   └── config_manager.py       # Gestor de configuración
│
├── gui/                        # Interfaz gráfica
│   ├── __init__.py
│   └── app_limones.py          # Aplicación tkinter
│
├── export/                     # Exportadores
│   ├── __init__.py
│   └── data_exporter.py        # Exportación CSV/JSON
│
├── utils/                      # Utilidades
│   └── __init__.py
│
└── database/                   # (Futuro) Historial
    └── __init__.py
```

## 📊 Fundamentos Matemáticos

### 1. Módulo de Entrada de Datos
```
Imagen → Tensor T ∈ ℝ^(m×n×3)
Descomposición: T = [M_R, M_G, M_B]
```

### 2. Módulo Cromático
```
Transformación RGB → HSV (cambio de base vectorial)
p = [R, G, B]ᵀ → p' = [H, S, V]ᵀ

Clasificación por umbrales de H (Tonalidad):
- Verde:    H ∈ [35, 85]°
- Pintón:   H ∈ [20, 35)°
- Amarillo: H ∈ [0, 20)°
```

### 3. Módulo Morfológico
```
Convolución con kernels de Sobel:
Gx = [[-1, 0, 1],      Gy = [[-1, -2, -1],
      [-2, 0, 2],            [ 0,  0,  0],
      [-1, 0, 1]]            [ 1,  2,  1]]

Magnitud del gradiente: G = √(Gx² + Gy²)
Rugosidad: R = σ²(G) / μ(G)
```

### 4. Vector de Características
```
v = [H_avg, C_rug, P_def]ᵀ ∈ ℝ³

Donde:
- H_avg: Promedio de Tonalidad (grados)
- C_rug: Coeficiente de Rugosidad (adimensional)
- P_def: Porcentaje de Defectos Superficiales (%)
```

### 5. Clasificación Final
```
Exportación Larga (30 días) ⟺ 
    (H_avg ≥ 20) ∧ (C_rug < 50) ∧ (P_def < 5%)

Consumo Local (7 días) ⟺ 
    ¬(Criterios de Exportación)
```

## 📈 Ejemplo de Salida

### Consola (Modo CLI)
```
============================================================
MÓDULO CROMÁTICO - Análisis de Tonalidad
============================================================
  Rango de Tonalidad (H): [0.00, 345.00]
  Promedio de Tonalidad: 27.34°
  Desviación estándar: 40.72°

  📊 Clasificación Cromática: Pintón
     Maduración media - Transición

============================================================
MÓDULO MORFOLÓGICO - Detección de Imperfecciones
============================================================
  Intensidad de bordes (promedio): 2.13
  Intensidad máxima: 172.19
  Coeficiente de Rugosidad: 70.3962
  Porcentaje de Defectos Superficiales: 0.60%

============================================================
VECTOR DE CARACTERÍSTICAS
============================================================
  v = [27.34, 70.3962, 0.60]ᵀ

============================================================
CLASIFICACIÓN DE CALIDAD Y VIDA ÚTIL
============================================================
  📋 Clasificación: CONSUMO LOCAL
  ⏱ Vida Útil Estimada: 7 días
  📝 Justificación: Alta rugosidad (70.40)
```

### Archivo JSON
```json
{
  "archivo": "limon_prueba.jpg",
  "vector_caracteristicas": {
    "tonalidad": 27.34,
    "rugosidad": 70.40,
    "defectos": 0.60
  },
  "clasificacion": "CONSUMO LOCAL",
  "vida_util_dias": 7,
  "justificacion": "Alta rugosidad (70.40)"
}
```

## ⌨️ Atajos de Teclado (Modo GUI)

| Atajo | Acción |
|-------|--------|
| `Ctrl+O` | Abrir imagen |
| `Ctrl+S` | Exportar PDF |
| `F5` | Reclasificar con nueva configuración |

## 🔧 Solución de Problemas

### Error: "No se pudo cargar la imagen"
- Verifique que el archivo existe
- Formatos soportados: JPG, PNG, BMP
- Intente con una ruta absoluta

### Error: "ModuleNotFoundError"
- Instale las dependencias: `py -m pip install numpy opencv-python matplotlib pillow`
- Verifique la versión de Python: `py --version`

### GUI no se inicia
- Verifique que tkinter esté instalado (viene con Python estándar)
- En Linux: `sudo apt-get install python3-tk`

## 🎓 Aplicaciones

- 🍋 Control de calidad en empaque de limones
- 📦 Clasificación automática para exportación
- 📊 Análisis estadístico de lotes
- 🔬 Investigación agroindustrial

## 🛠️ Desarrollo Futuro

### Mejoras Planificadas
- [ ] Generación de informes PDF con gráficos
- [ ] Procesamiento por lotes de múltiples imágenes
- [ ] Historial de clasificaciones con SQLite
- [ ] Detección automática de ROI (Region of Interest)
- [ ] Análisis de textura GLCM adicional
- [ ] Sistema de calibración con dataset etiquetado
- [ ] API REST para integración

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT.

## 👨‍💻 Autor

**Ingeniero Senior de Visión por Computadora**

Sistema desarrollado con fines académicos y de investigación agroindustrial.

---

**Versión**: 2.0 Professional  
**Fecha**: Febrero 2026  
**Tecnologías**: Python, NumPy, OpenCV, Matplotlib, tkinter
