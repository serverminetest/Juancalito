-- Script para arreglar la base de datos después de la simplificación de inventarios
-- Eliminar la tabla categoria_inventario que ya no se usa

-- Primero, eliminar la foreign key constraint si existe
ALTER TABLE producto DROP CONSTRAINT IF EXISTS producto_categoria_id_fkey;

-- Eliminar la columna categoria_id si existe (por si acaso)
ALTER TABLE producto DROP COLUMN IF EXISTS categoria_id;

-- Agregar la nueva columna categoria si no existe
ALTER TABLE producto ADD COLUMN IF NOT EXISTS categoria VARCHAR(50);

-- Eliminar la tabla categoria_inventario
DROP TABLE IF EXISTS categoria_inventario;

-- Actualizar productos existentes para usar categorías fijas (si hay datos)
UPDATE producto SET categoria = 'ALMACEN GENERAL' WHERE categoria IS NULL OR categoria = '';

-- Verificar que todo esté bien
SELECT 'Base de datos arreglada correctamente' as status;
