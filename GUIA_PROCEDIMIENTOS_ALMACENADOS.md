# 📘 Guía de Procedimientos Almacenados para Inventario

## 🎯 ¿Qué son los Procedimientos Almacenados?

Los procedimientos almacenados son **funciones que viven en la base de datos** y automatizan tareas complejas del inventario. Son **más rápidos, más seguros y más confiables** que hacer las operaciones manualmente.

---

## 📦 Instalación

### 1. Ejecutar el script en pgAdmin

1. Abre **pgAdmin**
2. Conecta a tu base de datos
3. Click derecho en tu base de datos → **Query Tool**
4. Abre el archivo `procedimientos_almacenados_inventario.sql`
5. Copia y pega todo el contenido
6. Click en **Execute** (⚡ o F5)
7. Verifica que diga: "Query returned successfully"

### 2. Ejecutar la migración de columnas

Antes de usar los procedimientos, asegúrate de ejecutar:

```sql
-- En pgAdmin, ejecuta:
\i migracion_saldo_inicial.sql
```

O copia el contenido de `migracion_saldo_inicial.sql` y ejecútalo.

---

## 🔧 Procedimientos Disponibles

### 1. **cerrar_mes_inventario(periodo)** 🔒
**¿Qué hace?**
- Recalcula todos los stocks del mes
- Marca el mes como cerrado (ya no se puede editar)
- Evita modificaciones accidentales

**Cuándo usarlo:**
- Al final de cada mes, antes de abrir el siguiente

**Ejemplo:**
```sql
-- Cerrar octubre 2025
SELECT * FROM cerrar_mes_inventario('2025-10');
```

**Resultado:**
```
productos_actualizados | productos_cerrados | mensaje
150                    | 150                | ✅ Mes 2025-10 cerrado exitosamente...
```

**Desde la aplicación:**
```
Ir a: Inventarios → [Botón "Cerrar Mes Octubre"]
```

---

### 2. **abrir_nuevo_mes_inventario(periodo)** 🆕
**¿Qué hace?**
- Copia TODOS los productos del mes anterior al nuevo mes
- El **saldo final del mes anterior** se convierte en **saldo inicial del nuevo mes**
- Cierra automáticamente el mes anterior
- Deja el nuevo mes listo para trabajar

**Cuándo usarlo:**
- Al inicio de cada mes nuevo

**Ejemplo:**
```sql
-- Abrir noviembre 2025 (copia desde octubre)
SELECT * FROM abrir_nuevo_mes_inventario('2025-11');
```

**Resultado:**
```
productos_copiados | periodo_origen | periodo_destino | mensaje
150                | 2025-10        | 2025-11         | ✅ Nuevo mes 2025-11 abierto...
```

**Importante:**
- Si ya existen productos en el mes nuevo, te dará error (no sobreescribe)
- Automáticamente cierra el mes anterior

---

### 3. **recalcular_stocks(periodo)** 🔄
**¿Qué hace?**
- Recalcula el stock de TODOS los productos del período
- Usa la fórmula: `Stock = Saldo Inicial + Entradas - Salidas`
- Detecta y corrige inconsistencias

**Cuándo usarlo:**
- Cuando sospechas que hay errores en los stocks
- Después de importar datos de Excel
- Como verificación mensual

**Ejemplo:**
```sql
-- Recalcular solo octubre
SELECT * FROM recalcular_stocks('2025-10');

-- Recalcular TODOS los meses
SELECT * FROM recalcular_stocks(NULL);
```

**Resultado:**
```
productos_recalculados | diferencias_encontradas | mensaje
150                    | 5                       | ✅ 150 productos recalculados. 5 diferencias corregidas.
```

---

### 4. **reporte_stock_bajo(periodo)** ⚠️
**¿Qué hace?**
- Lista TODOS los productos con stock por debajo del mínimo
- Ordena por urgencia (mayor diferencia primero)
- Incluye información del proveedor

**Cuándo usarlo:**
- Semanalmente para saber qué comprar
- Antes de cerrar el mes
- Cuando necesitas hacer pedidos

**Ejemplo:**
```sql
SELECT * FROM reporte_stock_bajo('2025-10');
```

**Resultado:**
```
codigo    | nombre          | categoria        | stock_actual | stock_minimo | diferencia | proveedor
ABC-001   | SULFATO         | QUIMICOS         | 5            | 20           | 15         | Química ABC
DEF-002   | CAJAS CARTON    | POSCOSECHA       | 10           | 50           | 40         | Empaques XYZ
```

**Desde la aplicación:**
```
Ir a: Inventarios → Reportes → [Ver Stock Bajo]
```

---

### 5. **estadisticas_mes(periodo)** 📊
**¿Qué hace?**
- Genera estadísticas completas del mes
- Total de productos, entradas, salidas
- Valor total del inventario
- Estado del mes (abierto/cerrado)

**Cuándo usarlo:**
- Para reportes mensuales
- Para presentaciones a gerencia
- Para análisis de tendencias

**Ejemplo:**
```sql
SELECT * FROM estadisticas_mes('2025-10');
```

**Resultado:**
```
total_productos | productos_activos | productos_stock_bajo | total_entradas | total_salidas | valor_total_inventario | mes_cerrado
150             | 148               | 12                   | 5000           | 3200          | 125000000.00           | TRUE
```

---

### 6. **auditoria_movimientos(periodo)** 🔍
**¿Qué hace?**
- Detecta movimientos sospechosos o con errores
- Encuentra salidas que exceden el stock
- Detecta cantidades inusualmente grandes
- Identifica salidas sin motivo

**Cuándo usarlo:**
- Antes de cerrar el mes
- Cuando sospechas errores de digitación
- Para auditorías internas

**Ejemplo:**
```sql
SELECT * FROM auditoria_movimientos('2025-10');
```

**Resultado:**
```
movimiento_id | producto_codigo | producto_nombre | tipo_movimiento | cantidad | fecha_movimiento     | problema
45            | ABC-001         | SULFATO         | SALIDA          | 100      | 2025-10-15 14:30:00  | Salida mayor al stock disponible
67            | DEF-002         | CAJAS           | ENTRADA         | 10000    | 2025-10-20 09:15:00  | Cantidad inusualmente grande
89            | GHI-003         | ALAMBRE         | SALIDA          | 50       | 2025-10-22 16:45:00  | Salida sin motivo especificado
```

---

### 7. **Vista: vista_kardex_completo** 📋
**¿Qué es?**
- Es una vista (tabla virtual) que muestra el kardex de TODOS los productos
- Se actualiza automáticamente
- Perfecta para exportar a Excel

**Cuándo usarla:**
- Para generar reportes
- Para exportar a Excel
- Para análisis en Power BI

**Ejemplo:**
```sql
-- Ver kardex de octubre
SELECT * FROM vista_kardex_completo WHERE periodo = '2025-10';

-- Ver solo productos con stock bajo
SELECT * FROM vista_kardex_completo WHERE estado_stock = 'STOCK BAJO';

-- Ver por categoría
SELECT * FROM vista_kardex_completo WHERE categoria = 'QUIMICOS' AND periodo = '2025-10';
```

**Resultado:**
```
codigo  | nombre   | categoria | periodo | saldo_inicial | total_entradas | total_salidas | saldo_final | estado_stock | valor_inventario
ABC-001 | SULFATO  | QUIMICOS  | 2025-10 | 50            | 100            | 80            | 70          | NORMAL       | 350000.00
```

---

## 🔄 Flujo de Trabajo Mensual (Proceso Completo)

### **Fin de Mes (Ejemplo: 31 de Octubre)**

```sql
-- PASO 1: Ver estadísticas antes de cerrar
SELECT * FROM estadisticas_mes('2025-10');

-- PASO 2: Ver productos con stock bajo
SELECT * FROM reporte_stock_bajo('2025-10');

-- PASO 3: Auditar movimientos sospechosos
SELECT * FROM auditoria_movimientos('2025-10');

-- PASO 4: Si hay errores, corregirlos manualmente y luego recalcular
SELECT * FROM recalcular_stocks('2025-10');

-- PASO 5: Cerrar el mes de octubre
SELECT * FROM cerrar_mes_inventario('2025-10');
```

### **Inicio de Mes (Ejemplo: 1 de Noviembre)**

```sql
-- PASO 6: Abrir el nuevo mes (copia automáticamente desde octubre)
SELECT * FROM abrir_nuevo_mes_inventario('2025-11');

-- PASO 7: Verificar que todo se copió correctamente
SELECT * FROM estadisticas_mes('2025-11');

-- PASO 8: Ver el kardex completo del nuevo mes
SELECT * FROM vista_kardex_completo WHERE periodo = '2025-11' LIMIT 20;
```

---

## 🌐 Uso Desde la Aplicación Web

Todas estas funciones están integradas en la aplicación Flask:

### **Rutas Disponibles:**

1. **Cerrar Mes:**
   ```
   POST /inventarios/procedimientos/cerrar-mes/2025-10
   ```

2. **Abrir Mes:**
   ```
   POST /inventarios/procedimientos/abrir-mes/2025-11
   ```

3. **Recalcular Stocks:**
   ```
   GET /inventarios/procedimientos/recalcular-stocks/2025-10
   ```

4. **Reporte Stock Bajo:**
   ```
   GET /inventarios/procedimientos/reporte-stock-bajo/2025-10
   ```

5. **Estadísticas:**
   ```
   GET /inventarios/procedimientos/estadisticas/2025-10
   ```

6. **Auditoría:**
   ```
   GET /inventarios/procedimientos/auditoria/2025-10
   ```

---

## ✅ Ventajas de Usar Procedimientos Almacenados

| Aspecto | Sin Procedimientos | Con Procedimientos |
|---------|-------------------|-------------------|
| **Velocidad** | Lento (Python procesa todo) | Rápido (PostgreSQL lo hace) |
| **Seguridad** | Múltiples pasos, propenso a errores | Todo o nada (transaccional) |
| **Consistencia** | Puede dejar datos inconsistentes | Garantiza consistencia |
| **Auditoría** | Difícil de rastrear | Registros claros |
| **Mantenimiento** | Cambios en múltiples lugares | Un solo lugar |

---

## 🚨 Precauciones

1. **SIEMPRE haz backup antes de cerrar un mes:**
   ```sql
   -- En pgAdmin:
   Herramientas → Backup
   ```

2. **No cierres un mes si hay movimientos pendientes de revisar**

3. **Verifica las estadísticas antes de cerrar**

4. **Solo los administradores deben ejecutar estos procedimientos**

---

## 🆘 Solución de Problemas

### Problema: "function cerrar_mes_inventario does not exist"
**Solución:** Ejecuta el script `procedimientos_almacenados_inventario.sql` en pgAdmin

### Problema: "column saldo_inicial does not exist"
**Solución:** Ejecuta el script `migracion_saldo_inicial.sql` primero

### Problema: "Ya existen productos en el período"
**Solución:** No puedes abrir un mes que ya existe. Elimina los productos o usa otro período.

### Problema: Los stocks no coinciden después de recalcular
**Solución:** 
1. Revisa la auditoría: `SELECT * FROM auditoria_movimientos('2025-10');`
2. Corrige los movimientos problemáticos
3. Vuelve a recalcular

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en la aplicación
2. Ejecuta la auditoría para detectar errores
3. Verifica que ejecutaste ambos scripts SQL
4. Asegúrate de tener permisos de administrador

---

**¡Los procedimientos almacenados hacen tu vida más fácil! 🚀**

