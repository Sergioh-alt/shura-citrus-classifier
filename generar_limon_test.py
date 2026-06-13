"""Script para generar imagen sintética de limón para pruebas"""
import numpy as np
from PIL import Image, ImageDraw
import cv2

# Crear imagen de 600x600
width, height = 600, 600
image = Image.new('RGB', (width, height), (255, 255, 255))
draw = ImageDraw.Draw(image)

# Dibujar un círculo amarillo-verdoso (limón)
center_x, center_y = width // 2, height // 2
radius = 200

# Crear gradiente para simular textura del limón
for r in range(radius, 0, -1):
    # Color amarillo-verdoso con gradación
    yellow = 255
    green = int(255 - (radius - r) * 0.3)
    red = int(200 + (radius - r) * 0.2)
    
    color = (red, green, 50)  # RGB
    draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], 
                 fill=color, outline=color)

# Agregar algunas "imperfecciones" para simular textura real
np.random.seed(42)
for _ in range(50):
    x = np.random.randint(center_x - radius + 50, center_x + radius - 50)
    y = np.random.randint(center_y - radius + 50, center_y + radius - 50)
    
    # Verificar que está dentro del círculo
    if (x - center_x)**2 + (y - center_y)**2 < radius**2:
        spot_size = np.random.randint(2, 8)
        color = (np.random.randint(180, 220), np.random.randint(200, 240), np.random.randint(30, 70))
        draw.ellipse([x - spot_size, y - spot_size, x + spot_size, y + spot_size],
                    fill=color)

# Guardar imagen
image.save('limon_prueba.jpg', 'JPEG', quality=95)
print("✓ Imagen de limón generada exitosamente: limon_prueba.jpg")
