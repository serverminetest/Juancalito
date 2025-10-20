-- ============================================
-- DIAGNÓSTICO: Valor Total de Inventario
-- ============================================
-- Este script ayuda a identificar qué productos están inflando el valor total

-- 1. Ver productos con mayor valor en inventario
SELECT 
    codigo,
    nombre,
    categoria,
    periodo,
    stock_actual,
    precio_unitario,
    (stock_actual * precio_unitario) AS valor_total,
    proveedor
FROM producto
WHERE periodo = '2025-10'  -- Cambia al período que quieras revisar
  AND activo = TRUE
ORDER BY (stock_actual * precio_unitario) DESC
LIMIT 20;

-- 2. Ver productos con precio unitario muy alto (posiblemente errores)
SELECT 
    codigo,
    nombre,
    categoria,
    periodo,
    stock_actual,
    precio_unitario,
    (stock_actual * precio_unitario) AS valor_total
FROM producto
WHERE periodo = '2025-10'
  AND precio_unitario > 1000000  -- Precios mayores a $1,000,000
ORDER BY precio_unitario DESC;

-- 3. Ver productos con stock muy alto (posiblemente errores)
SELECT 
    codigo,
    nombre,
    categoria,
    periodo,
    stock_actual,
    precio_unitario,
    (stock_actual * precio_unitario) AS valor_total
FROM producto
WHERE periodo = '2025-10'
  AND stock_actual > 10000  -- Stock mayor a 10,000 unidades
ORDER BY stock_actual DESC;

-- 4. Valor total por categoría
SELECT 
    categoria,
    COUNT(*) AS total_productos,
    SUM(stock_actual) AS stock_total,
    SUM(stock_actual * precio_unitario) AS valor_total,
    AVG(precio_unitario) AS precio_promedio
FROM producto
WHERE periodo = '2025-10'
  AND activo = TRUE
GROUP BY categoria
ORDER BY valor_total DESC;

-- 5. Ver productos con precio = 0
SELECT 
    COUNT(*) AS productos_sin_precio
FROM producto
WHERE periodo = '2025-10'
  AND activo = TRUE
  AND (precio_unitario = 0 OR precio_unitario IS NULL);

-- 6. Ver distribución de precios
SELECT 
    CASE 
        WHEN precio_unitario = 0 THEN 'Sin precio ($0)'
        WHEN precio_unitario < 1000 THEN 'Muy bajo (< $1,000)'
        WHEN precio_unitario < 10000 THEN 'Bajo ($1K - $10K)'
        WHEN precio_unitario < 100000 THEN 'Medio ($10K - $100K)'
        WHEN precio_unitario < 1000000 THEN 'Alto ($100K - $1M)'
        ELSE 'Muy alto (> $1M)'
    END AS rango_precio,
    COUNT(*) AS cantidad_productos,
    SUM(stock_actual * precio_unitario) AS valor_total
FROM producto
WHERE periodo = '2025-10'
  AND activo = TRUE
GROUP BY 
    CASE 
        WHEN precio_unitario = 0 THEN 'Sin precio ($0)'
        WHEN precio_unitario < 1000 THEN 'Muy bajo (< $1,000)'
        WHEN precio_unitario < 10000 THEN 'Bajo ($1K - $10K)'
        WHEN precio_unitario < 100000 THEN 'Medio ($10K - $100K)'
        WHEN precio_unitario < 1000000 THEN 'Alto ($100K - $1M)'
        ELSE 'Muy alto (> $1M)'
    END
ORDER BY 
    CASE 
        WHEN precio_unitario = 0 THEN 1
        WHEN precio_unitario < 1000 THEN 2
        WHEN precio_unitario < 10000 THEN 3
        WHEN precio_unitario < 100000 THEN 4
        WHEN precio_unitario < 1000000 THEN 5
        ELSE 6
    END;

-- 7. PROCEDIMIENTO ALMACENADO: Corregir precios anormales
CREATE OR REPLACE FUNCTION corregir_precios_anormales(
    periodo_corregir VARCHAR(7),
    precio_maximo NUMERIC DEFAULT 10000000  -- $10 millones como máximo por defecto
)
RETURNS TABLE(
    productos_corregidos INTEGER,
    mensaje TEXT
) AS $$
DECLARE
    v_productos_corregidos INTEGER := 0;
BEGIN
    -- Marcar como $0 los precios excesivamente altos (probablemente errores)
    UPDATE producto
    SET precio_unitario = 0
    WHERE periodo = periodo_corregir
      AND precio_unitario > precio_maximo;
    
    GET DIAGNOSTICS v_productos_corregidos = ROW_COUNT;
    
    RETURN QUERY SELECT 
        v_productos_corregidos,
        format('✅ %s productos con precios anormales corregidos a $0', v_productos_corregidos)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Ejemplo de uso:
-- SELECT * FROM corregir_precios_anormales('2025-10', 5000000);  -- Corrige precios > $5M


-- ============================================
-- SOLUCIONES RÁPIDAS
-- ============================================

-- OPCIÓN A: Corregir manualmente un producto específico
-- UPDATE producto SET precio_unitario = 50000 WHERE codigo = 'ABC-001' AND periodo = '2025-10';

-- OPCIÓN B: Poner todos los precios en $0 para un período
-- UPDATE producto SET precio_unitario = 0 WHERE periodo = '2025-10' AND precio_unitario IS NULL;

-- OPCIÓN C: Corregir precios automáticamente (productos con precio > $10M a $0)
-- SELECT * FROM corregir_precios_anormales('2025-10', 10000000);

