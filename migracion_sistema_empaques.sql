-- Migración para Sistema de Ingreso Flexible por Empaques
-- Fecha: 2025-01-20

-- 1. Agregar columnas a la tabla movimiento_inventario
ALTER TABLE movimiento_inventario 
ADD COLUMN tipo_ingreso VARCHAR(20) DEFAULT 'INDIVIDUAL',
ADD COLUMN cantidad_empaques INTEGER DEFAULT NULL,
ADD COLUMN contenido_por_empaque DECIMAL(10,2) DEFAULT NULL,
ADD COLUMN precio_por_empaque DECIMAL(15,2) DEFAULT NULL;

-- 2. Agregar comentarios para documentar las columnas
COMMENT ON COLUMN movimiento_inventario.tipo_ingreso IS 'Tipo de ingreso: EMPAQUE o INDIVIDUAL';
COMMENT ON COLUMN movimiento_inventario.cantidad_empaques IS 'Cantidad de empaques cuando tipo_ingreso = EMPAQUE';
COMMENT ON COLUMN movimiento_inventario.contenido_por_empaque IS 'Contenido por empaque (ej: 20L, 5KG)';
COMMENT ON COLUMN movimiento_inventario.precio_por_empaque IS 'Precio por empaque cuando tipo_ingreso = EMPAQUE';

-- 3. Agregar índices para mejorar rendimiento
CREATE INDEX idx_movimiento_tipo_ingreso ON movimiento_inventario(tipo_ingreso);
CREATE INDEX idx_movimiento_empaques ON movimiento_inventario(cantidad_empaques) WHERE cantidad_empaques IS NOT NULL;

-- 4. Actualizar movimientos existentes para que sean tipo INDIVIDUAL
UPDATE movimiento_inventario 
SET tipo_ingreso = 'INDIVIDUAL' 
WHERE tipo_ingreso IS NULL;

-- 5. Agregar restricciones de validación
ALTER TABLE movimiento_inventario 
ADD CONSTRAINT chk_tipo_ingreso 
CHECK (tipo_ingreso IN ('EMPAQUE', 'INDIVIDUAL'));

ALTER TABLE movimiento_inventario 
ADD CONSTRAINT chk_empaques_requeridos 
CHECK (
    (tipo_ingreso = 'EMPAQUE' AND cantidad_empaques IS NOT NULL AND contenido_por_empaque IS NOT NULL AND precio_por_empaque IS NOT NULL) OR
    (tipo_ingreso = 'INDIVIDUAL' AND cantidad_empaques IS NULL AND contenido_por_empaque IS NULL AND precio_por_empaque IS NULL)
);

-- 6. Crear vista para reportes de movimientos con información completa
CREATE OR REPLACE VIEW vista_movimientos_detallados AS
SELECT 
    mi.id,
    mi.producto_id,
    p.codigo,
    p.nombre,
    p.categoria,
    mi.periodo,
    mi.tipo_movimiento,
    mi.tipo_ingreso,
    mi.cantidad,
    mi.cantidad_empaques,
    mi.contenido_por_empaque,
    mi.precio_unitario,
    mi.precio_por_empaque,
    mi.total,
    mi.motivo,
    mi.referencia,
    mi.responsable,
    mi.observaciones,
    mi.fecha_movimiento,
    -- Cálculos automáticos
    CASE 
        WHEN mi.tipo_ingreso = 'EMPAQUE' THEN mi.cantidad_empaques * mi.contenido_por_empaque
        ELSE mi.cantidad
    END as cantidad_total_unidad_base,
    CASE 
        WHEN mi.tipo_ingreso = 'EMPAQUE' THEN mi.cantidad_empaques * mi.precio_por_empaque
        ELSE mi.total
    END as valor_total_calculado,
    u.username as usuario_creacion
FROM movimiento_inventario mi
JOIN producto p ON mi.producto_id = p.id
LEFT JOIN "user" u ON mi.created_by = u.id
ORDER BY mi.fecha_movimiento DESC;

-- 7. Función para calcular totales por tipo de ingreso
CREATE OR REPLACE FUNCTION calcular_totales_movimiento(
    p_tipo_ingreso VARCHAR(20),
    p_cantidad INTEGER,
    p_cantidad_empaques INTEGER,
    p_contenido_por_empaque DECIMAL(10,2),
    p_precio_unitario DECIMAL(15,2),
    p_precio_por_empaque DECIMAL(15,2)
) RETURNS TABLE(
    cantidad_total INTEGER,
    valor_total DECIMAL(15,2)
) AS $$
BEGIN
    IF p_tipo_ingreso = 'EMPAQUE' THEN
        RETURN QUERY SELECT 
            (p_cantidad_empaques * p_contenido_por_empaque)::INTEGER as cantidad_total,
            (p_cantidad_empaques * p_precio_por_empaque) as valor_total;
    ELSE
        RETURN QUERY SELECT 
            p_cantidad as cantidad_total,
            (p_cantidad * p_precio_unitario) as valor_total;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 8. Procedimiento para validar consistencia de datos
CREATE OR REPLACE PROCEDURE validar_consistencia_empaques()
AS $$
DECLARE
    inconsistencias INTEGER;
BEGIN
    -- Verificar que los totales calculados coincidan con los guardados
    SELECT COUNT(*) INTO inconsistencias
    FROM movimiento_inventario mi
    WHERE mi.tipo_ingreso = 'EMPAQUE' 
    AND mi.total != (mi.cantidad_empaques * mi.precio_por_empaque);
    
    IF inconsistencias > 0 THEN
        RAISE NOTICE 'Se encontraron % inconsistencias en movimientos por empaques', inconsistencias;
    ELSE
        RAISE NOTICE 'Todos los movimientos por empaques son consistentes';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 9. Actualizar estadísticas de la tabla
ANALYZE movimiento_inventario;

-- 10. Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'Migración completada exitosamente. Sistema de empaques habilitado.';
    RAISE NOTICE 'Nuevas columnas agregadas: tipo_ingreso, cantidad_empaques, contenido_por_empaque, precio_por_empaque';
    RAISE NOTICE 'Vista creada: vista_movimientos_detallados';
    RAISE NOTICE 'Función creada: calcular_totales_movimiento';
    RAISE NOTICE 'Procedimiento creado: validar_consistencia_empaques';
END
$$;
