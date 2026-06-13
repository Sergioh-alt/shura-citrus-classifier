"""
Test de Base de Datos y DAO
"""

import sys
sys.path.insert(0, '.')

from database.dao import LimonDAO, AlertaDAO

print("=== Test de DAO ===\n")

# Test LimonDAO
limon_dao = LimonDAO()

print("1. Guardando limones de prueba...")
for i in range(5):
    limon_id = limon_dao.guardar(
        tonalidad=20 + i*5,
        rugosidad=40 + i*10,
        defectos=1.0 + i,
        acidez=4.0 + i*0.5,
        grupo_asignado=['Brasil', 'Europa', 'Local Premium', 'Industrial', 'Descarte'][i],
        salida_fisica=i+1,
        clasificacion_original='EXPORTACION',
        vida_util_dias=20 + i*5
    )
    print(f"   Limón {i+1} guardado (ID: {limon_id})")

print("\n2. Obteniendo últimos limones...")
ultimos = limon_dao.obtener_ultimos(limit=3)
for limon in ultimos:
    print(f"   ID {limon['id']}: {limon['grupo_asignado']} - Acidez: {limon['acidez']}%")

print("\n3. Contando por grupo...")
conteo = limon_dao.contar_por_grupo()
for grupo, total in conteo.items():
    print(f"   {grupo}: {total}")

print("\n4. Estadísticas generales...")
stats = limon_dao.obtener_estadisticas()
print(f"   Total: {stats['total']}")
print(f"   Acidez promedio: {stats['promedio_acidez']}%")

# Test AlertaDAO
print("\n5. Creando alertas...")
alerta_dao = AlertaDAO()

alerta_dao.crear('hardware', 'warning', 'Test de alerta')
alertas = alerta_dao.obtener_activas()
print(f"   Alertas activas: {len(alertas)}")

print("\n✅ Tests de DAO completados")
