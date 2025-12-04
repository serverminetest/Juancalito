-- =====================================================
-- Script SQL para actualizar la tabla solicitud_empleado
-- Sistema de Solicitudes de Empleados - Flores Juncalito SAS
-- =====================================================

-- Agregar columna para datos adicionales (JSON)
ALTER TABLE solicitud_empleado 
ADD COLUMN IF NOT EXISTS datos_adicionales TEXT;

-- Hacer que fecha_fin sea opcional (nullable)
ALTER TABLE solicitud_empleado 
ALTER COLUMN fecha_fin DROP NOT NULL;

-- Agregar comentario a la nueva columna
COMMENT ON COLUMN solicitud_empleado.datos_adicionales IS 'Datos adicionales específicos según el tipo de solicitud almacenados como JSON';

-- Verificar que los cambios se aplicaron correctamente
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'solicitud_empleado'
    AND column_name IN ('datos_adicionales', 'fecha_fin')
ORDER BY ordinal_position;

