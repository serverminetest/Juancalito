-- Script para actualizar la tabla empleado
-- Hacer email_personal opcional (nullable)
-- Agregar campos de fecha y lugar de expedición del documento

-- Hacer email_personal nullable
ALTER TABLE empleado 
ALTER COLUMN email_personal DROP NOT NULL;

-- Agregar campo fecha_expedicion_documento
ALTER TABLE empleado 
ADD COLUMN IF NOT EXISTS fecha_expedicion_documento DATE;

-- Agregar campo lugar_expedicion_documento
ALTER TABLE empleado 
ADD COLUMN IF NOT EXISTS lugar_expedicion_documento VARCHAR(200);

-- Agregar comentarios para documentación
COMMENT ON COLUMN empleado.email_personal IS 'Email personal del empleado (opcional)';
COMMENT ON COLUMN empleado.fecha_expedicion_documento IS 'Fecha de expedición del documento de identidad';
COMMENT ON COLUMN empleado.lugar_expedicion_documento IS 'Lugar de expedición del documento de identidad';
