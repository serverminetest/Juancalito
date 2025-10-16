-- Migración para agregar columna 'periodo' al sistema de inventarios mensuales
-- Ejecutar este script en pgAdmin

-- 1. Agregar columna 'periodo' a la tabla 'producto'
ALTER TABLE producto ADD COLUMN IF NOT EXISTS periodo VARCHAR(7);

-- 2. Agregar columna 'periodo' a la tabla 'movimiento_inventario'  
ALTER TABLE movimiento_inventario ADD COLUMN IF NOT EXISTS periodo VARCHAR(7);

-- 3. Asignar período actual (2025-10) a productos existentes que tengan periodo NULL
UPDATE producto 
SET periodo = '2025-10' 
WHERE periodo IS NULL;

-- 4. Asignar período actual (2025-10) a movimientos existentes que tengan periodo NULL
UPDATE movimiento_inventario 
SET periodo = '2025-10' 
WHERE periodo IS NULL;

-- 5. Hacer la columna 'periodo' NOT NULL después de asignar valores
ALTER TABLE producto ALTER COLUMN periodo SET NOT NULL;
ALTER TABLE movimiento_inventario ALTER COLUMN periodo SET NOT NULL;

-- 6. Agregar índice único para evitar códigos duplicados en el mismo período y categoría
-- (Esto permitirá el mismo código en diferentes meses/categorías)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = '_producto_codigo_categoria_periodo_uc'
    ) THEN
        ALTER TABLE producto ADD CONSTRAINT _producto_codigo_categoria_periodo_uc 
        UNIQUE (codigo, categoria, periodo);
    END IF;
END $$;

-- 7. Verificar que las columnas se agregaron correctamente
SELECT 
    'producto' as tabla,
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'producto' AND column_name = 'periodo'

UNION ALL

SELECT 
    'movimiento_inventario' as tabla,
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'movimiento_inventario' AND column_name = 'periodo';

-- 8. Mostrar estadísticas de productos por período
SELECT 
    periodo,
    COUNT(*) as total_productos,
    COUNT(DISTINCT categoria) as categorias_con_productos
FROM producto 
GROUP BY periodo 
ORDER BY periodo;
