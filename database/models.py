"""
Modelos de Base de Datos usando SQLAlchemy
Sistema de Clasificación de Limones v3.0
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text, Date, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()


class Limon(Base):
    """
    Modelo para limones clasificados.
    """
    __tablename__ = 'limones'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Vector de características
    tonalidad = Column(Float, nullable=False)
    rugosidad = Column(Float, nullable=False)
    defectos = Column(Float, nullable=False)
    acidez = Column(Float, nullable=False)
    
    # Clasificación
    grupo_asignado = Column(String(100), nullable=False)
    salida_fisica = Column(Integer, nullable=False)
    clasificacion_original = Column(String(100))
    vida_util_dias = Column(Integer)
    
    # Metadata
    imagen_path = Column(String(500))
    thumbnail = Column(LargeBinary)
    operador = Column(String(100), default='automatico')
    modo = Column(String(50), default='automatico')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    verificaciones = relationship('VerificacionManual', back_populates='limon', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'tonalidad': self.tonalidad,
            'rugosidad': self.rugosidad,
            'defectos': self.defectos,
            'acidez': self.acidez,
            'grupo_asignado': self.grupo_asignado,
            'salida_fisica': self.salida_fisica,
            'clasificacion_original': self.clasificacion_original,
            'vida_util_dias': self.vida_util_dias,
            'operador': self.operador,
            'modo': self.modo
        }


class Alerta(Base):
    """
    Modelo para alertas del sistema.
    """
    __tablename__ = 'alertas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    tipo = Column(String(50), nullable=False)
    severidad = Column(String(20), nullable=False)
    mensaje = Column(Text, nullable=False)
    detalles = Column(Text)
    
    resuelta = Column(Boolean, default=False)
    resolucion_timestamp = Column(DateTime)
    resolucion_nota = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'tipo': self.tipo,
            'severidad': self.severidad,
            'mensaje': self.mensaje,
            'detalles': self.detalles,
            'resuelta': self.resuelta,
            'resolucion_timestamp': self.resolucion_timestamp.isoformat() if self.resolucion_timestamp else None
        }


class EstadisticaHoraria(Base):
    """
    Modelo para estadísticas agregadas por hora.
    """
    __tablename__ = 'estadisticas_horarias'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    hora = Column(Integer, nullable=False)
    
    total_procesados = Column(Integer, default=0)
    promedio_acidez = Column(Float)
    promedio_rugosidad = Column(Float)
    promedio_defectos = Column(Float)
    porcentaje_descarte = Column(Float)
    throughput = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'hora': self.hora,
            'total_procesados': self.total_procesados,
            'promedio_acidez': self.promedio_acidez,
            'promedio_rugosidad': self.promedio_rugosidad,
            'promedio_defectos': self.promedio_defectos,
            'porcentaje_descarte': self.porcentaje_descarte,
            'throughput': self.throughput
        }


class VerificacionManual(Base):
    """
    Modelo para verificaciones manuales (control de calidad).
    """
    __tablename__ = 'verificaciones_manuales'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    limon_id = Column(Integer, ForeignKey('limones.id', ondelete='CASCADE'), nullable=False)
    
    clasificacion_automatica = Column(String(100), nullable=False)
    clasificacion_manual = Column(String(100), nullable=False)
    correcto = Column(Boolean, nullable=False)
    
    notas = Column(Text)
    operador = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    limon = relationship('Limon', back_populates='verificaciones')
    
    def to_dict(self):
        return {
            'id': self.id,
            'limon_id': self.limon_id,
            'clasificacion_automatica': self.clasificacion_automatica,
            'clasificacion_manual': self.clasificacion_manual,
            'correcto': self.correcto,
            'notas': self.notas,
            'operador': self.operador,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Perfil(Base):
    """
    Modelo para perfiles de configuración guardados.
    """
    __tablename__ = 'perfiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)
    
    config_json = Column(Text, nullable=False)
    grupos_json = Column(Text, nullable=False)
    
    activo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_config(self):
        """Obtener configuración como diccionario"""
        return json.loads(self.config_json) if self.config_json else {}
    
    def get_grupos(self):
        """Obtener grupos como diccionario"""
        return json.loads(self.grupos_json) if self.grupos_json else {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'activo': self.activo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Funciones de utilidad para crear/conectar a la base de datos

def create_database(db_path='database/clasificacion.db'):
    """
    Crear base de datos y todas las tablas.
    
    Args:
        db_path: Ruta al archivo de base de datos
    
    Returns:
        Engine de SQLAlchemy
    """
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    print(f"✓ Base de datos creada: {db_path}")
    return engine


def get_session(db_path='database/clasificacion.db'):
    """
    Obtener sesión de base de datos.
    
    Args:
        db_path: Ruta al archivo de base de datos
    
    Returns:
        Session de SQLAlchemy
    """
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    # Test: crear base de datos
    import os
    
    # Crear directorio si no existe
    os.makedirs('database', exist_ok=True)
    
    # Crear base de datos
    engine = create_database()
    
    # Verificar tablas
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tablas = inspector.get_table_names()
    
    print(f"\n✓ Tablas creadas ({len(tablas)}):")
    for tabla in tablas:
        print(f"  - {tabla}")
    
    # Test de inserción
    session = get_session()
    
    # Crear limón de prueba
    limon_test = Limon(
        tonalidad=27.34,
        rugosidad=70.40,
        defectos=0.60,
        acidez=5.17,
        grupo_asignado='Procesamiento Industrial',
        salida_fisica=4,
        clasificacion_original='CONSUMO LOCAL',
        vida_util_dias=7
    )
    
    session.add(limon_test)
    session.commit()
    
    print(f"\n✓ Limón de prueba insertado (ID: {limon_test.id})")
    
    # Leer limón
    limon_recuperado = session.query(Limon).first()
    print(f"✓ Limón recuperado: {limon_recuperado.to_dict()}")
    
    session.close()
    
    print("\n✅ Test de base de datos completado")
