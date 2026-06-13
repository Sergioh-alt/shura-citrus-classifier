-- Schema para Base de Datos de Clasificación de Limones
-- Versión 3.0

-- Tabla principal: limones clasificados
CREATE TABLE IF NOT EXISTS limones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Vector de características
    tonalidad REAL NOT NULL,
    rugosidad REAL NOT NULL,
    defectos REAL NOT NULL,
    acidez REAL NOT NULL,
    
    -- Clasificación
    grupo_asignado TEXT NOT NULL,
    salida_fisica INTEGER NOT NULL,
    clasificacion_original TEXT,
    vida_util_dias INTEGER,
    
    -- Metadata
    imagen_path TEXT,
    thumbnail BLOB,
    operador TEXT DEFAULT 'automatico',
    modo TEXT DEFAULT 'automatico',  -- 'automatico', 'manual', 'verificado'
    
    -- Auditoría
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de alertas del sistema
CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    tipo TEXT NOT NULL,  -- 'hardware', 'camara', 'calidad', 'sistema'
    severidad TEXT NOT NULL,  -- 'info', 'warning', 'error', 'critical'
    mensaje TEXT NOT NULL,
    detalles TEXT,
    
    resuelta BOOLEAN DEFAULT FALSE,
    resolucion_timestamp DATETIME,
    resolucion_nota TEXT
);

-- Tabla de estadísticas agregadas por hora
CREATE TABLE IF NOT EXISTS estadisticas_horarias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL,
    hora INTEGER NOT NULL,
    
    total_procesados INTEGER DEFAULT 0,
    promedio_acidez REAL,
    promedio_rugosidad REAL,
    promedio_defectos REAL,
    porcentaje_descarte REAL,
    throughput REAL,  -- limones/minuto
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(fecha, hora)
);

-- Tabla de verificaciones manuales (control de calidad)
CREATE TABLE IF NOT EXISTS verificaciones_manuales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    limon_id INTEGER NOT NULL,
    
    clasificacion_automatica TEXT NOT NULL,
    clasificacion_manual TEXT NOT NULL,
    correcto BOOLEAN NOT NULL,
    
    notas TEXT,
    operador TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (limon_id) REFERENCES limones(id) ON DELETE CASCADE
);

-- Tabla de configuraciones/perfiles guardados
CREATE TABLE IF NOT EXISTS perfiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT,
    
    config_json TEXT NOT NULL,  -- JSON serializado
    grupos_json TEXT NOT NULL,  -- JSON serializado
    
    activo BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_limones_timestamp ON limones(timestamp);
CREATE INDEX IF NOT EXISTS idx_limones_grupo ON limones(grupo_asignado);
CREATE INDEX IF NOT EXISTS idx_limones_fecha ON limones(date(timestamp));

CREATE INDEX IF NOT EXISTS idx_alertas_timestamp ON alertas(timestamp);
CREATE INDEX IF NOT EXISTS idx_alertas_tipo ON alertas(tipo);
CREATE INDEX IF NOT EXISTS idx_alertas_severidad ON alertas(severidad);
CREATE INDEX IF NOT EXISTS idx_alertas_resuelta ON alertas(resuelta);

CREATE INDEX IF NOT EXISTS idx_stats_fecha_hora ON estadisticas_horarias(fecha, hora);

CREATE INDEX IF NOT EXISTS idx_verificaciones_limon ON verificaciones_manuales(limon_id);
CREATE INDEX IF NOT EXISTS idx_verificaciones_correcto ON verificaciones_manuales(correcto);

-- Vista para estadísticas por grupo
CREATE VIEW IF NOT EXISTS vista_estadisticas_grupos AS
SELECT 
    grupo_asignado,
    COUNT(*) as total,
    AVG(acidez) as acidez_promedio,
    AVG(rugosidad) as rugosidad_promedio,
    AVG(defectos) as defectos_promedio,
    MIN(timestamp) as primer_registro,
    MAX(timestamp) as ultimo_registro
FROM limones
GROUP BY grupo_asignado;

-- Vista para alertas activas
CREATE VIEW IF NOT EXISTS vista_alertas_activas AS
SELECT 
    id,
    timestamp,
    tipo,
    severidad,
    mensaje,
    detalles,
    julianday('now') - julianday(timestamp) as dias_desde_alerta
FROM alertas
WHERE resuelta = FALSE
ORDER BY severidad DESC, timestamp DESC;

-- Vista para exactitud del sistema (control de calidad)
CREATE VIEW IF NOT EXISTS vista_exactitud_sistema AS
SELECT 
    COUNT(*) as total_verificaciones,
    SUM(CASE WHEN correcto = 1 THEN 1 ELSE 0 END) as correctos,
    ROUND(100.0 * SUM(CASE WHEN correcto = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as porcentaje_exactitud,
    clasificacion_automatica,
    COUNT(*) as frecuencia
FROM verificaciones_manuales
GROUP BY clasificacion_automatica;
