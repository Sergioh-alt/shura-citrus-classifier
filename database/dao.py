"""
Data Access Object (DAO) para Base de Datos
Operaciones CRUD y consultas especializadas
"""

from database.models import (
    Limon, Alerta, EstadisticaHoraria, VerificacionManual, Perfil,
    get_session
)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, desc
from typing import List, Dict, Optional
import numpy as np


class LimonDAO:
    """DAO para limones clasificados"""
    
    def __init__(self, db_path='database/clasificacion.db'):
        self.db_path = db_path
    
    def guardar(self, tonalidad: float, rugosidad: float, defectos: float, acidez: float,
                grupo_asignado: str, salida_fisica: int, clasificacion_original: str = None,
                vida_util_dias: int = None, imagen_path: str = None, thumbnail: bytes = None,
                operador: str = 'automatico', modo: str = 'automatico') -> int:
        """
        Guardar nuevo limón clasificado.
        
        Returns:
            ID del limón guardado
        """
        session = get_session(self.db_path)
        
        try:
            limon = Limon(
                tonalidad=tonalidad,
                rugosidad=rugosidad,
                defectos=defectos,
                acidez=acidez,
                grupo_asignado=grupo_asignado,
                salida_fisica=salida_fisica,
                clasificacion_original=clasificacion_original,
                vida_util_dias=vida_util_dias,
                imagen_path=imagen_path,
                thumbnail=thumbnail,
                operador=operador,
                modo=modo
            )
            
            session.add(limon)
            session.commit()
            limon_id = limon.id
            
            return limon_id
        finally:
            session.close()
    
    def obtener_por_id(self, limon_id: int) -> Optional[Dict]:
        """Obtener limón por ID"""
        session = get_session(self.db_path)
        
        try:
            limon = session.query(Limon).filter(Limon.id == limon_id).first()
            return limon.to_dict() if limon else None
        finally:
            session.close()
    
    def obtener_ultimos(self, limit: int = 100) -> List[Dict]:
        """Obtener últimos N limones"""
        session = get_session(self.db_path)
        
        try:
            limones = session.query(Limon).order_by(desc(Limon.timestamp)).limit(limit).all()
            return [l.to_dict() for l in limones]
        finally:
            session.close()
    
    def obtener_por_fecha(self, fecha: date) -> List[Dict]:
        """Obtener limones de una fecha específica"""
        session = get_session(self.db_path)
        
        try:
            limones = session.query(Limon).filter(
                func.date(Limon.timestamp) == fecha
            ).all()
            return [l.to_dict() for l in limones]
        finally:
            session.close()
    
    def contar_por_grupo(self, fecha_inicio: date = None, fecha_fin: date = None) -> Dict:
        """Contar limones por grupo en un rango de fechas"""
        session = get_session(self.db_path)
        
        try:
            query = session.query(
                Limon.grupo_asignado,
                func.count(Limon.id).label('total')
            )
            
            if fecha_inicio and fecha_fin:
                query = query.filter(
                    and_(
                        func.date(Limon.timestamp) >= fecha_inicio,
                        func.date(Limon.timestamp) <= fecha_fin
                    )
                )
            
            resultado = query.group_by(Limon.grupo_asignado).all()
            
            return {grupo: total for grupo, total in resultado}
        finally:
            session.close()
    
    def obtener_estadisticas(self, fecha_inicio: date = None, fecha_fin: date = None) -> Dict:
        """Obtener estadísticas generales"""
        session = get_session(self.db_path)
        
        try:
            query = session.query(Limon)
            
            if fecha_inicio and fecha_fin:
                query = query.filter(
                    and_(
                        func.date(Limon.timestamp) >= fecha_inicio,
                        func.date(Limon.timestamp) <= fecha_fin
                    )
                )
            
            total = query.count()
            
            if total == 0:
                return {
                    'total': 0,
                    'promedio_acidez': 0,
                    'promedio_rugosidad': 0,
                    'promedio_defectos': 0
                }
            
            stats = query.with_entities(
                func.avg(Limon.acidez).label('acidez_avg'),
                func.avg(Limon.rugosidad).label('rugosidad_avg'),
                func.avg(Limon.defectos).label('defectos_avg')
            ).first()
            
            return {
                'total': total,
                'promedio_acidez': round(stats.acidez_avg, 2) if stats.acidez_avg else 0,
                'promedio_rugosidad': round(stats.rugosidad_avg, 2) if stats.rugosidad_avg else 0,
                'promedio_defectos': round(stats.defectos_avg, 2) if stats.defectos_avg else 0
            }
        finally:
            session.close()


class AlertaDAO:
    """DAO para alertas del sistema"""
    
    def __init__(self, db_path='database/clasificacion.db'):
        self.db_path = db_path
    
    def crear(self, tipo: str, severidad: str, mensaje: str, detalles: str = None) -> int:
        """Crear nueva alerta"""
        session = get_session(self.db_path)
        
        try:
            alerta = Alerta(
                tipo=tipo,
                severidad=severidad,
                mensaje=mensaje,
                detalles=detalles
            )
            
            session.add(alerta)
            session.commit()
            return alerta.id
        finally:
            session.close()
    
    def obtener_activas(self, severidad: str = None) -> List[Dict]:
        """Obtener alertas activas (no resueltas)"""
        session = get_session(self.db_path)
        
        try:
            query = session.query(Alerta).filter(Alerta.resuelta == False)
            
            if severidad:
                query = query.filter(Alerta.severidad == severidad)
            
            alertas = query.order_by(desc(Alerta.timestamp)).all()
            return [a.to_dict() for a in alertas]
        finally:
            session.close()
    
    def resolver(self, alerta_id: int, nota: str = None):
        """Marcar alerta como resuelta"""
        session = get_session(self.db_path)
        
        try:
            alerta = session.query(Alerta).filter(Alerta.id == alerta_id).first()
            
            if alerta:
                alerta.resuelta = True
                alerta.resolucion_timestamp = datetime.utcnow()
                alerta.resolucion_nota = nota
                session.commit()
        finally:
            session.close()


class EstadisticaHorariaDAO:
    """DAO para estadísticas horarias"""
    
    def __init__(self, db_path='database/clasificacion.db'):
        self.db_path = db_path
    
    def actualizar_estadisticas(self, fecha: date, hora: int):
        """Calcular y actualizar estadísticas para una hora específica"""
        session = get_session(self.db_path)
        
        try:
            # Obtener limones de esa hora
            limones = session.query(Limon).filter(
                and_(
                    func.date(Limon.timestamp) == fecha,
                    func.extract('hour', Limon.timestamp) == hora
                )
            ).all()
            
            if not limones:
                return
            
            total = len(limones)
            acidez_promedio = np.mean([l.acidez for l in limones])
            rugosidad_promedio = np.mean([l.rugosidad for l in limones])
            defectos_promedio = np.mean([l.defectos for l in limones])
            
            descarte_count = len([l for l in limones if l.grupo_asignado == 'Descarte'])
            porcentaje_descarte = (descarte_count / total) * 100 if total > 0 else 0
            
            # Throughput (asumiendo 60 minutos)
            throughput = total / 60.0
            
            # Buscar o crear registro
            stat = session.query(EstadisticaHoraria).filter(
                and_(
                    EstadisticaHoraria.fecha == fecha,
                    EstadisticaHoraria.hora == hora
                )
            ).first()
            
            if stat:
                # Actualizar
                stat.total_procesados = total
                stat.promedio_acidez = acidez_promedio
                stat.promedio_rugosidad = rugosidad_promedio
                stat.promedio_defectos = defectos_promedio
                stat.porcentaje_descarte = porcentaje_descarte
                stat.throughput = throughput
            else:
                # Crear nuevo
                stat = EstadisticaHoraria(
                    fecha=fecha,
                    hora=hora,
                    total_procesados=total,
                    promedio_acidez=acidez_promedio,
                    promedio_rugosidad=rugosidad_promedio,
                    promedio_defectos=defectos_promedio,
                    porcentaje_descarte=porcentaje_descarte,
                    throughput=throughput
                )
                session.add(stat)
            
            session.commit()
        finally:
            session.close()
    
    def obtener_por_fecha(self, fecha: date) -> List[Dict]:
        """Obtener estadísticas de un día"""
        session = get_session(self.db_path)
        
        try:
            stats = session.query(EstadisticaHoraria).filter(
                EstadisticaHoraria.fecha == fecha
            ).order_by(EstadisticaHoraria.hora).all()
            
            return [s.to_dict() for s in stats]
        finally:
            session.close()


# Test del DAO
if __name__ == "__main__":
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
    
    print("\n2. Obteniendo últimos 3 limones...")
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
    print(f"   Rugosidad promedio: {stats['promedio_rugosidad']}")
    
    # Test AlertaDAO
    print("\n5. Creando alertas...")
    alerta_dao = AlertaDAO()
    
    alerta_dao.crear('hardware', 'warning', 'FPS bajo detectado')
    alerta_dao.crear('sistema', 'info', 'Sistema iniciado correctamente')
    
    alertas = alerta_dao.obtener_activas()
    print(f"   Alertas activas: {len(alertas)}")
    
    print("\n✅ Tests de DAO completados")
