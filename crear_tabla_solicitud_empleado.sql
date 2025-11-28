-- =====================================================
-- Script SQL para crear la tabla solicitud_empleado
-- Sistema de Solicitudes de Empleados - Flores Juncalito SAS
-- =====================================================

-- Crear la tabla solicitud_empleado
CREATE TABLE IF NOT EXISTS solicitud_empleado (
    id SERIAL PRIMARY KEY,
    
    -- Relación con empleado
    empleado_id INTEGER NOT NULL REFERENCES empleado(id) ON DELETE CASCADE,
    
    -- Tipo de solicitud
    tipo_solicitud VARCHAR(50) NOT NULL,
    
    -- Fechas
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    
    -- Información de la solicitud
    motivo TEXT NOT NULL,
    observaciones TEXT,
    
    -- Estado de la solicitud
    estado VARCHAR(20) DEFAULT 'PENDIENTE',
    
    -- Aprobación/Rechazo
    aprobado_por_id INTEGER REFERENCES "user"(id) ON DELETE SET NULL,
    fecha_aprobacion TIMESTAMP WITHOUT TIME ZONE,
    comentario_admin TEXT,
    
    -- Archivos adjuntos del empleado (almacenados como BYTEA)
    adjuntos_data BYTEA,
    adjuntos_nombres TEXT,
    
    -- Documentos del admin (respuesta)
    documentos_admin_data BYTEA,
    documentos_admin_nombres TEXT,
    
    -- Campos del sistema
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejorar el rendimiento de las consultas
CREATE INDEX IF NOT EXISTS idx_solicitud_empleado_empleado_id ON solicitud_empleado(empleado_id);
CREATE INDEX IF NOT EXISTS idx_solicitud_empleado_estado ON solicitud_empleado(estado);
CREATE INDEX IF NOT EXISTS idx_solicitud_empleado_tipo ON solicitud_empleado(tipo_solicitud);
CREATE INDEX IF NOT EXISTS idx_solicitud_empleado_fecha_inicio ON solicitud_empleado(fecha_inicio);
CREATE INDEX IF NOT EXISTS idx_solicitud_empleado_created_at ON solicitud_empleado(created_at);
CREATE INDEX IF NOT EXISTS idx_solicitud_empleado_aprobado_por ON solicitud_empleado(aprobado_por_id);

-- Agregar comentarios a la tabla y columnas para documentación
COMMENT ON TABLE solicitud_empleado IS 'Tabla para gestionar solicitudes de empleados (vacaciones, licencias, permisos, etc.)';
COMMENT ON COLUMN solicitud_empleado.tipo_solicitud IS 'Tipo de solicitud: VACACIONES, PERMISO_REMUNERADO, LICENCIA_LUTO, CALAMIDAD, INCAPACIDAD';
COMMENT ON COLUMN solicitud_empleado.estado IS 'Estado de la solicitud: PENDIENTE, APROBADA, RECHAZADA';
COMMENT ON COLUMN solicitud_empleado.adjuntos_data IS 'Archivos adjuntos del empleado almacenados como BYTEA (JSON serializado)';
COMMENT ON COLUMN solicitud_empleado.documentos_admin_data IS 'Documentos del administrador almacenados como BYTEA (JSON serializado)';

-- Verificar que la tabla se creó correctamente
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'solicitud_empleado'
ORDER BY ordinal_position;

