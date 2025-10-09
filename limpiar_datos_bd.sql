-- ============================================================
-- SCRIPT SQL PARA LIMPIAR DATOS DE LA BASE DE DATOS
-- ============================================================
-- 
-- 🧹 Este script elimina TODOS los datos excepto usuarios
-- 🔄 Reinicia los IDs para que comiencen desde 1
-- 
-- ⚠️ ADVERTENCIA: Este script es IRREVERSIBLE
-- ⚠️ Solo ejecutar si estás ABSOLUTAMENTE seguro
--
-- ============================================================

-- Deshabilitar restricciones de clave foránea temporalmente
SET session_replication_role = replica;

-- ============================================================
-- 🗑️ ELIMINAR DATOS DE TODAS LAS TABLAS (excepto user)
-- ============================================================

-- Eliminar datos de asistencia
DELETE FROM asistencia;

-- Eliminar datos de visitantes
DELETE FROM visitante;

-- Eliminar datos de notificaciones
DELETE FROM notificacion;

-- Eliminar datos de productos
DELETE FROM producto;

-- Eliminar datos de movimientos de inventario
DELETE FROM movimiento_inventario;

-- Eliminar datos de categorías de inventario (excepto las por defecto)
DELETE FROM categoria_inventario 
WHERE nombre NOT IN ('ALMACEN GENERAL', 'QUIMICOS', 'POSCOSECHA');

-- Eliminar datos de contratos generados
DELETE FROM contrato_generado;

-- Eliminar datos de contratos
DELETE FROM contrato;

-- Eliminar datos de empleados
DELETE FROM empleado;

-- ============================================================
-- 🔄 REINICIAR SECUENCIAS (IDs) PARA QUE COMIENCEN DESDE 1
-- ============================================================

-- Reiniciar secuencia de empleados
ALTER SEQUENCE empleado_id_seq RESTART WITH 1;

-- Reiniciar secuencia de contratos
ALTER SEQUENCE contrato_id_seq RESTART WITH 1;

-- Reiniciar secuencia de asistencias (si existe)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'asistencia_id_seq') THEN
        ALTER SEQUENCE asistencia_id_seq RESTART WITH 1;
    END IF;
END $$;

-- Reiniciar secuencia de visitantes (si existe)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'visitante_id_seq') THEN
        ALTER SEQUENCE visitante_id_seq RESTART WITH 1;
    END IF;
END $$;

-- Reiniciar secuencia de notificaciones (si existe)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'notificacion_id_seq') THEN
        ALTER SEQUENCE notificacion_id_seq RESTART WITH 1;
    END IF;
END $$;

-- Reiniciar secuencia de productos (si existe)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'producto_id_seq') THEN
        ALTER SEQUENCE producto_id_seq RESTART WITH 1;
    END IF;
END $$;

-- Reiniciar secuencia de categorías de inventario (si existe)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'categoria_inventario_id_seq') THEN
        ALTER SEQUENCE categoria_inventario_id_seq RESTART WITH 1;
    END IF;
END $$;

-- Reiniciar secuencia de movimientos de inventario (si existe)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'movimiento_inventario_id_seq') THEN
        ALTER SEQUENCE movimiento_inventario_id_seq RESTART WITH 1;
    END IF;
END $$;

-- Reiniciar secuencia de contratos generados (si existe)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'contrato_generado_id_seq') THEN
        ALTER SEQUENCE contrato_generado_id_seq RESTART WITH 1;
    END IF;
END $$;

-- ============================================================
-- ✅ VERIFICACIÓN FINAL
-- ============================================================

-- Mostrar conteo de registros restantes
SELECT 'user' as tabla, COUNT(*) as registros FROM "user"
UNION ALL
SELECT 'empleado' as tabla, COUNT(*) as registros FROM empleado
UNION ALL
SELECT 'contrato' as tabla, COUNT(*) as registros FROM contrato
UNION ALL
SELECT 'categoria_inventario' as tabla, COUNT(*) as registros FROM categoria_inventario
UNION ALL
SELECT 'producto' as tabla, COUNT(*) as registros FROM producto
UNION ALL
SELECT 'asistencia' as tabla, COUNT(*) as registros FROM asistencia
UNION ALL
SELECT 'visitante' as tabla, COUNT(*) as registros FROM visitante
UNION ALL
SELECT 'notificacion' as tabla, COUNT(*) as registros FROM notificacion
UNION ALL
SELECT 'contrato_generado' as tabla, COUNT(*) as registros FROM contrato_generado;

-- ============================================================
-- 🎉 LIMPIEZA COMPLETADA
-- ============================================================
-- 
-- ✅ Datos eliminados:
--    - Todos los empleados
--    - Todos los contratos
--    - Todas las asistencias
--    - Todos los visitantes
--    - Todo el inventario (excepto categorías por defecto)
--    - Todas las notificaciones
--    - Todos los contratos generados
--
-- ✅ Secuencias reiniciadas:
--    - Todos los IDs comenzarán desde 1
--
-- ✅ Datos conservados:
--    - Usuarios administradores
--    - Categorías de inventario por defecto
--
-- ============================================================
