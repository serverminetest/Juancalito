-- ============================================
-- MIGRACIÓN: Sistema de Saldo Inicial y Cierre Mensual
-- ============================================
-- Este script agrega las columnas necesarias para el sistema mejorado de inventarios
-- Ejecutar en pgAdmin o en tu herramienta de PostgreSQL

-- 1. Agregar columna 'saldo_inicial' a la tabla 'producto'
ALTER TABLE producto ADD COLUMN IF NOT EXISTS saldo_inicial INTEGER DEFAULT 0;

-- 2. Agregar columna 'mes_cerrado' a la tabla 'producto'
ALTER TABLE producto ADD COLUMN IF NOT EXISTS mes_cerrado BOOLEAN DEFAULT FALSE;

-- 3. Actualizar saldo_inicial con el stock_actual actual de cada producto
-- (Esto es para productos existentes que no tienen saldo_inicial)
UPDATE producto 
SET saldo_inicial = stock_actual 
WHERE saldo_inicial IS NULL OR saldo_inicial = 0;

-- 4. Opcional: Si quieres recalcular el stock_actual basado en movimientos
-- (Descomenta estas líneas solo si quieres recalcular todo desde cero)

/*
-- Recalcular stock_actual para cada producto basado en:
-- saldo_inicial + entradas - salidas
UPDATE producto p
SET stock_actual = (
    SELECT COALESCE(p.saldo_inicial, 0) + 
           COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'ENTRADA' THEN m.cantidad ELSE 0 END), 0) -
           COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'SALIDA' THEN m.cantidad ELSE 0 END), 0)
    FROM movimiento_inventario m
    WHERE m.producto_id = p.id
);
*/

-- 5. Verificar la estructura actualizada
SELECT 
    codigo,
    nombre,
    categoria,
    periodo,
    saldo_inicial,
    stock_actual,
    mes_cerrado
FROM producto
ORDER BY categoria, codigo
LIMIT 10;

-- ============================================
-- NOTAS IMPORTANTES:
-- ============================================
-- 
-- 1. 'saldo_inicial': Es el saldo al inicio del período (mes)
--    - Cuando copias un mes nuevo, el saldo final del mes anterior
--      se convierte en el saldo inicial del nuevo mes
--
-- 2. 'stock_actual': Se calcula automáticamente como:
--    stock_actual = saldo_inicial + entradas - salidas
--
-- 3. 'mes_cerrado': Indica si el período está cerrado
--    - TRUE: No se puede editar (solo admin)
--    - FALSE: Se puede editar normalmente
--
-- 4. El sistema ahora funciona así:
--    - Octubre 2025: saldo_inicial = 100, entradas = 50, salidas = 30
--      → stock_actual = 100 + 50 - 30 = 120
--    - Al copiar a Noviembre 2025:
--      → Noviembre saldo_inicial = 120 (saldo final de Octubre)
--      → Octubre mes_cerrado = TRUE (para evitar cambios)
--
-- ============================================

