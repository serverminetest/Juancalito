#!/usr/bin/env python3
"""
Script para actualizar la tabla contrato_generado y agregar la columna archivo_data
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def actualizar_tabla_contratos():
    """Actualizar tabla contrato_generado para agregar columna archivo_data"""
    
    # Obtener URL de la base de datos
    database_url = os.environ.get('DATABASE_PUBLIC_URL')
    if not database_url:
        print("❌ Error: DATABASE_PUBLIC_URL no configurada")
        return False
    
    try:
        print("🚀 Actualizando tabla contrato_generado...")
        print("=" * 50)
        
        # Conectar a la base de datos
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("✅ Conectado a la base de datos")
        
        # Verificar si la columna archivo_data ya existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'contrato_generado' 
            AND column_name = 'archivo_data';
        """)
        
        if cursor.fetchone():
            print("✅ La columna archivo_data ya existe")
        else:
            print("📝 Agregando columna archivo_data...")
            cursor.execute("""
                ALTER TABLE contrato_generado 
                ADD COLUMN archivo_data BYTEA;
            """)
            print("✅ Columna archivo_data agregada")
        
        # Eliminar todos los contratos generados existentes (sin datos binarios)
        cursor.execute("SELECT COUNT(*) FROM contrato_generado;")
        count_antes = cursor.fetchone()[0]
        
        if count_antes > 0:
            print(f"🗑️ Eliminando {count_antes} contratos generados existentes (sin datos binarios)...")
            cursor.execute("DELETE FROM contrato_generado;")
            print("✅ Contratos existentes eliminados")
        
        # Confirmar cambios
        conn.commit()
        
        print("=" * 50)
        print("🎉 ¡Actualización completada exitosamente!")
        print("📋 Resumen:")
        print(f"   - Columna archivo_data: ✅ Agregada/Verificada")
        print(f"   - Contratos antiguos eliminados: {count_antes}")
        print("   - Tabla lista para nuevos contratos con datos binarios")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la actualización: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 Conexión cerrada")

if __name__ == "__main__":
    print("🔧 Actualizador de Tabla de Contratos Generados")
    print("=" * 50)
    
    if actualizar_tabla_contratos():
        print("\n✅ ¡Proceso completado exitosamente!")
        print("💡 Ahora puedes generar nuevos contratos que se guardarán correctamente.")
    else:
        print("\n❌ El proceso falló. Revisa los errores arriba.")
