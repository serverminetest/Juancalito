-- ============================================
-- PROCEDIMIENTOS ALMACENADOS PARA INVENTARIO
-- ============================================
-- Estos procedimientos automatizan operaciones complejas del inventario mensual
-- Ejecutar en pgAdmin o en tu herramienta de PostgreSQL

-- ============================================
-- 1. PROCEDIMIENTO: Cerrar Mes de Inventario
-- ============================================
-- Cierra un período de inventario para evitar modificaciones
-- Recalcula todos los stocks finales antes de cerrar

CREATE OR REPLACE FUNCTION cerrar_mes_inventario(periodo_a_cerrar VARCHAR(7))
RETURNS TABLE(
    productos_actualizados INTEGER,
    productos_cerrados INTEGER,
    mensaje TEXT
) AS $$
DECLARE
    v_productos_actualizados INTEGER := 0;
    v_productos_cerrados INTEGER := 0;
BEGIN
    -- 1. Recalcular stock_actual de todos los productos del período
    UPDATE producto p
    SET stock_actual = (
        SELECT COALESCE(p.saldo_inicial, 0) + 
               COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'ENTRADA' THEN m.cantidad ELSE 0 END), 0) -
               COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'SALIDA' THEN m.cantidad ELSE 0 END), 0)
        FROM movimiento_inventario m
        WHERE m.producto_id = p.id AND m.periodo = periodo_a_cerrar
    )
    WHERE p.periodo = periodo_a_cerrar;
    
    GET DIAGNOSTICS v_productos_actualizados = ROW_COUNT;
    
    -- 2. Marcar todos los productos del período como cerrados
    UPDATE producto
    SET mes_cerrado = TRUE
    WHERE periodo = periodo_a_cerrar;
    
    GET DIAGNOSTICS v_productos_cerrados = ROW_COUNT;
    
    -- 3. Retornar resultados
    RETURN QUERY SELECT 
        v_productos_actualizados,
        v_productos_cerrados,
        format('✅ Mes %s cerrado exitosamente. %s productos actualizados y cerrados.', 
               periodo_a_cerrar, v_productos_cerrados)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Ejemplo de uso:
-- SELECT * FROM cerrar_mes_inventario('2025-10');


-- ============================================
-- 2. PROCEDIMIENTO: Abrir Nuevo Mes (Copiar del Anterior)
-- ============================================
-- Copia productos del mes anterior al nuevo mes
-- Establece saldo_inicial = saldo_final del mes anterior

CREATE OR REPLACE FUNCTION abrir_nuevo_mes_inventario(periodo_nuevo VARCHAR(7))
RETURNS TABLE(
    productos_copiados INTEGER,
    periodo_origen VARCHAR(7),
    periodo_destino VARCHAR(7),
    mensaje TEXT
) AS $$
DECLARE
    v_periodo_anterior VARCHAR(7);
    v_año_nuevo INTEGER;
    v_mes_nuevo INTEGER;
    v_año_anterior INTEGER;
    v_mes_anterior INTEGER;
    v_productos_copiados INTEGER := 0;
    v_productos_existentes INTEGER;
BEGIN
    -- 1. Calcular período anterior
    v_año_nuevo := CAST(SPLIT_PART(periodo_nuevo, '-', 1) AS INTEGER);
    v_mes_nuevo := CAST(SPLIT_PART(periodo_nuevo, '-', 2) AS INTEGER);
    
    IF v_mes_nuevo = 1 THEN
        v_mes_anterior := 12;
        v_año_anterior := v_año_nuevo - 1;
    ELSE
        v_mes_anterior := v_mes_nuevo - 1;
        v_año_anterior := v_año_nuevo;
    END IF;
    
    v_periodo_anterior := LPAD(v_año_anterior::TEXT, 4, '0') || '-' || LPAD(v_mes_anterior::TEXT, 2, '0');
    
    -- 2. Verificar si ya existen productos en el nuevo período
    SELECT COUNT(*) INTO v_productos_existentes
    FROM producto
    WHERE periodo = periodo_nuevo;
    
    IF v_productos_existentes > 0 THEN
        RETURN QUERY SELECT 
            0,
            v_periodo_anterior,
            periodo_nuevo,
            format('❌ Error: Ya existen %s productos en el período %s', 
                   v_productos_existentes, periodo_nuevo)::TEXT;
        RETURN;
    END IF;
    
    -- 3. Copiar productos del mes anterior al nuevo mes
    INSERT INTO producto (
        codigo, nombre, descripcion, categoria, periodo, unidad_medida,
        precio_unitario, stock_minimo, saldo_inicial, stock_actual,
        ubicacion, proveedor, fecha_vencimiento, lote, activo, mes_cerrado
    )
    SELECT 
        p.codigo,
        p.nombre,
        p.descripcion,
        p.categoria,
        periodo_nuevo, -- Nuevo período
        p.unidad_medida,
        p.precio_unitario,
        p.stock_minimo,
        -- Saldo inicial = Saldo final del mes anterior
        COALESCE(p.saldo_inicial, 0) + 
        COALESCE((
            SELECT SUM(CASE WHEN m.tipo_movimiento = 'ENTRADA' THEN m.cantidad ELSE 0 END) -
                   SUM(CASE WHEN m.tipo_movimiento = 'SALIDA' THEN m.cantidad ELSE 0 END)
            FROM movimiento_inventario m
            WHERE m.producto_id = p.id
        ), 0) AS saldo_inicial,
        -- Stock actual = Saldo inicial (sin movimientos aún)
        COALESCE(p.saldo_inicial, 0) + 
        COALESCE((
            SELECT SUM(CASE WHEN m.tipo_movimiento = 'ENTRADA' THEN m.cantidad ELSE 0 END) -
                   SUM(CASE WHEN m.tipo_movimiento = 'SALIDA' THEN m.cantidad ELSE 0 END)
            FROM movimiento_inventario m
            WHERE m.producto_id = p.id
        ), 0) AS stock_actual,
        p.ubicacion,
        p.proveedor,
        p.fecha_vencimiento,
        p.lote,
        TRUE, -- activo
        FALSE -- mes_cerrado (nuevo mes está abierto)
    FROM producto p
    WHERE p.periodo = v_periodo_anterior AND p.activo = TRUE;
    
    GET DIAGNOSTICS v_productos_copiados = ROW_COUNT;
    
    -- 4. Cerrar el mes anterior automáticamente
    UPDATE producto
    SET mes_cerrado = TRUE
    WHERE periodo = v_periodo_anterior;
    
    -- 5. Retornar resultados
    RETURN QUERY SELECT 
        v_productos_copiados,
        v_periodo_anterior,
        periodo_nuevo,
        format('✅ Nuevo mes %s abierto exitosamente. %s productos copiados desde %s. Mes anterior cerrado.', 
               periodo_nuevo, v_productos_copiados, v_periodo_anterior)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Ejemplo de uso:
-- SELECT * FROM abrir_nuevo_mes_inventario('2025-11');


-- ============================================
-- 3. PROCEDIMIENTO: Recalcular Stock de Todos los Productos
-- ============================================
-- Recalcula el stock_actual basado en saldo_inicial + entradas - salidas
-- Útil para corregir inconsistencias

CREATE OR REPLACE FUNCTION recalcular_stocks(periodo_a_recalcular VARCHAR(7) DEFAULT NULL)
RETURNS TABLE(
    productos_recalculados INTEGER,
    diferencias_encontradas INTEGER,
    mensaje TEXT
) AS $$
DECLARE
    v_productos_recalculados INTEGER := 0;
    v_diferencias INTEGER := 0;
BEGIN
    -- Crear tabla temporal con stocks recalculados
    CREATE TEMP TABLE IF NOT EXISTS temp_stocks AS
    SELECT 
        p.id,
        p.stock_actual AS stock_anterior,
        COALESCE(p.saldo_inicial, 0) + 
        COALESCE((
            SELECT SUM(CASE WHEN m.tipo_movimiento = 'ENTRADA' THEN m.cantidad ELSE 0 END) -
                   SUM(CASE WHEN m.tipo_movimiento = 'SALIDA' THEN m.cantidad ELSE 0 END)
            FROM movimiento_inventario m
            WHERE m.producto_id = p.id
        ), 0) AS stock_nuevo
    FROM producto p
    WHERE (periodo_a_recalcular IS NULL OR p.periodo = periodo_a_recalcular);
    
    -- Contar diferencias
    SELECT COUNT(*) INTO v_diferencias
    FROM temp_stocks
    WHERE stock_anterior != stock_nuevo;
    
    -- Actualizar stocks
    UPDATE producto p
    SET stock_actual = t.stock_nuevo
    FROM temp_stocks t
    WHERE p.id = t.id;
    
    GET DIAGNOSTICS v_productos_recalculados = ROW_COUNT;
    
    -- Limpiar tabla temporal
    DROP TABLE IF EXISTS temp_stocks;
    
    -- Retornar resultados
    RETURN QUERY SELECT 
        v_productos_recalculados,
        v_diferencias,
        format('✅ %s productos recalculados. %s diferencias corregidas.', 
               v_productos_recalculados, v_diferencias)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Ejemplo de uso:
-- SELECT * FROM recalcular_stocks('2025-10');  -- Recalcular solo octubre
-- SELECT * FROM recalcular_stocks();           -- Recalcular todos


-- ============================================
-- 4. PROCEDIMIENTO: Reporte de Stock Bajo por Período
-- ============================================
-- Obtiene productos con stock por debajo del mínimo

CREATE OR REPLACE FUNCTION reporte_stock_bajo(periodo_reporte VARCHAR(7))
RETURNS TABLE(
    codigo VARCHAR(50),
    nombre VARCHAR(200),
    categoria VARCHAR(50),
    stock_actual INTEGER,
    stock_minimo INTEGER,
    diferencia INTEGER,
    proveedor VARCHAR(200)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.codigo,
        p.nombre,
        p.categoria,
        p.stock_actual,
        p.stock_minimo,
        (p.stock_minimo - p.stock_actual) AS diferencia,
        p.proveedor
    FROM producto p
    WHERE p.periodo = periodo_reporte
      AND p.activo = TRUE
      AND p.stock_actual < p.stock_minimo
    ORDER BY (p.stock_minimo - p.stock_actual) DESC;
END;
$$ LANGUAGE plpgsql;

-- Ejemplo de uso:
-- SELECT * FROM reporte_stock_bajo('2025-10');


-- ============================================
-- 5. PROCEDIMIENTO: Estadísticas del Mes
-- ============================================
-- Obtiene estadísticas completas de un período

CREATE OR REPLACE FUNCTION estadisticas_mes(periodo_stats VARCHAR(7))
RETURNS TABLE(
    total_productos INTEGER,
    productos_activos INTEGER,
    productos_stock_bajo INTEGER,
    total_entradas BIGINT,
    total_salidas BIGINT,
    valor_total_inventario NUMERIC,
    mes_cerrado BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER AS total_productos,
        COUNT(*) FILTER (WHERE p.activo = TRUE)::INTEGER AS productos_activos,
        COUNT(*) FILTER (WHERE p.stock_actual < p.stock_minimo AND p.activo = TRUE)::INTEGER AS productos_stock_bajo,
        COALESCE(SUM((
            SELECT SUM(m.cantidad)
            FROM movimiento_inventario m
            WHERE m.producto_id = p.id AND m.tipo_movimiento = 'ENTRADA'
        )), 0)::BIGINT AS total_entradas,
        COALESCE(SUM((
            SELECT SUM(m.cantidad)
            FROM movimiento_inventario m
            WHERE m.producto_id = p.id AND m.tipo_movimiento = 'SALIDA'
        )), 0)::BIGINT AS total_salidas,
        COALESCE(SUM(p.stock_actual * p.precio_unitario), 0)::NUMERIC AS valor_total_inventario,
        bool_and(p.mes_cerrado) AS mes_cerrado
    FROM producto p
    WHERE p.periodo = periodo_stats;
END;
$$ LANGUAGE plpgsql;

-- Ejemplo de uso:
-- SELECT * FROM estadisticas_mes('2025-10');


-- ============================================
-- 6. PROCEDIMIENTO: Auditoría de Movimientos Sospechosos
-- ============================================
-- Detecta movimientos que podrían ser errores

CREATE OR REPLACE FUNCTION auditoria_movimientos(periodo_audit VARCHAR(7))
RETURNS TABLE(
    movimiento_id INTEGER,
    producto_codigo VARCHAR(50),
    producto_nombre VARCHAR(200),
    tipo_movimiento VARCHAR(20),
    cantidad INTEGER,
    fecha_movimiento TIMESTAMP,
    problema TEXT
) AS $$
BEGIN
    RETURN QUERY
    -- Salidas que exceden el stock disponible
    SELECT 
        m.id,
        p.codigo,
        p.nombre,
        m.tipo_movimiento,
        m.cantidad,
        m.fecha_movimiento,
        'Salida mayor al stock disponible'::TEXT AS problema
    FROM movimiento_inventario m
    JOIN producto p ON p.id = m.producto_id
    WHERE m.periodo = periodo_audit
      AND m.tipo_movimiento = 'SALIDA'
      AND m.cantidad > (
          SELECT COALESCE(p2.saldo_inicial, 0) +
                 COALESCE(SUM(CASE WHEN m2.tipo_movimiento = 'ENTRADA' THEN m2.cantidad ELSE 0 END), 0) -
                 COALESCE(SUM(CASE WHEN m2.tipo_movimiento = 'SALIDA' AND m2.id < m.id THEN m2.cantidad ELSE 0 END), 0)
          FROM movimiento_inventario m2
          JOIN producto p2 ON p2.id = m2.producto_id
          WHERE m2.producto_id = m.producto_id
      )
    
    UNION ALL
    
    -- Movimientos con cantidades muy grandes (posibles errores de digitación)
    SELECT 
        m.id,
        p.codigo,
        p.nombre,
        m.tipo_movimiento,
        m.cantidad,
        m.fecha_movimiento,
        'Cantidad inusualmente grande'::TEXT AS problema
    FROM movimiento_inventario m
    JOIN producto p ON p.id = m.producto_id
    WHERE m.periodo = periodo_audit
      AND m.cantidad > 1000
    
    UNION ALL
    
    -- Movimientos sin motivo en salidas
    SELECT 
        m.id,
        p.codigo,
        p.nombre,
        m.tipo_movimiento,
        m.cantidad,
        m.fecha_movimiento,
        'Salida sin motivo especificado'::TEXT AS problema
    FROM movimiento_inventario m
    JOIN producto p ON p.id = m.producto_id
    WHERE m.periodo = periodo_audit
      AND m.tipo_movimiento = 'SALIDA'
      AND (m.motivo IS NULL OR m.motivo = '')
    
    ORDER BY fecha_movimiento DESC;
END;
$$ LANGUAGE plpgsql;

-- Ejemplo de uso:
-- SELECT * FROM auditoria_movimientos('2025-10');


-- ============================================
-- 7. VISTA: Kardex Completo (Para Reportes)
-- ============================================
-- Vista que muestra el kardex de todos los productos

CREATE OR REPLACE VIEW vista_kardex_completo AS
SELECT 
    p.codigo,
    p.nombre,
    p.categoria,
    p.periodo,
    p.saldo_inicial,
    COALESCE((
        SELECT SUM(m.cantidad)
        FROM movimiento_inventario m
        WHERE m.producto_id = p.id AND m.tipo_movimiento = 'ENTRADA'
    ), 0) AS total_entradas,
    COALESCE((
        SELECT SUM(m.cantidad)
        FROM movimiento_inventario m
        WHERE m.producto_id = p.id AND m.tipo_movimiento = 'SALIDA'
    ), 0) AS total_salidas,
    p.stock_actual AS saldo_final,
    p.stock_minimo,
    CASE 
        WHEN p.stock_actual < p.stock_minimo THEN 'STOCK BAJO'
        WHEN p.stock_actual = 0 THEN 'SIN STOCK'
        ELSE 'NORMAL'
    END AS estado_stock,
    p.precio_unitario,
    (p.stock_actual * p.precio_unitario) AS valor_inventario,
    p.mes_cerrado
FROM producto p
WHERE p.activo = TRUE
ORDER BY p.categoria, p.codigo;

-- Ejemplo de uso:
-- SELECT * FROM vista_kardex_completo WHERE periodo = '2025-10';
-- SELECT * FROM vista_kardex_completo WHERE estado_stock = 'STOCK BAJO';


-- ============================================
-- EJEMPLOS DE USO MENSUAL
-- ============================================

/*
-- ===== FLUJO TÍPICO DE FIN DE MES =====

-- 1. Ver estadísticas del mes actual antes de cerrar
SELECT * FROM estadisticas_mes('2025-10');

-- 2. Ver productos con stock bajo antes de cerrar
SELECT * FROM reporte_stock_bajo('2025-10');

-- 3. Auditar movimientos sospechosos
SELECT * FROM auditoria_movimientos('2025-10');

-- 4. Recalcular todos los stocks por si acaso
SELECT * FROM recalcular_stocks('2025-10');

-- 5. Cerrar el mes de octubre
SELECT * FROM cerrar_mes_inventario('2025-10');

-- 6. Abrir el nuevo mes de noviembre (copia automáticamente desde octubre)
SELECT * FROM abrir_nuevo_mes_inventario('2025-11');

-- 7. Verificar que todo se copió correctamente
SELECT * FROM estadisticas_mes('2025-11');

-- 8. Ver el kardex completo del nuevo mes
SELECT * FROM vista_kardex_completo WHERE periodo = '2025-11';
*/


-- ============================================
-- NOTAS IMPORTANTES
-- ============================================
-- 
-- 1. Estos procedimientos son seguros y atómicos (todo o nada)
-- 2. Úsalos al final de cada mes para automatizar el proceso
-- 3. Los procedimientos validan datos antes de ejecutar cambios
-- 4. Puedes llamarlos desde Python/Flask si lo prefieres
-- 5. La vista vista_kardex_completo es útil para reportes Excel
-- 
-- ============================================

