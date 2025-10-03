#!/usr/bin/env python3
"""
Script para arreglar los contratos generados existentes
"""

import os
import sys
from sqlalchemy import create_engine, text

def arreglar_contratos():
    """Arreglar contratos generados existentes"""
    
    # Obtener URL de la base de datos
    database_url = os.environ.get('DATABASE_PUBLIC_URL')
    if not database_url:
        print("❌ Error: DATABASE_PUBLIC_URL no configurada")
        return False
    
    try:
        print("🚀 Arreglando contratos generados...")
        print("=" * 50)
        
        # Conectar a la base de datos
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("✅ Conectado a la base de datos")
            
            # Verificar si la columna archivo_data existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'contrato_generado' 
                AND column_name = 'archivo_data';
            """))
            
            if result.fetchone():
                print("✅ La columna archivo_data ya existe")
            else:
                print("📝 Agregando columna archivo_data...")
                conn.execute(text("""
                    ALTER TABLE contrato_generado 
                    ADD COLUMN archivo_data BYTEA;
                """))
                print("✅ Columna archivo_data agregada")
            
            # Contar contratos existentes
            result = conn.execute(text("SELECT COUNT(*) FROM contrato_generado;"))
            count_antes = result.fetchone()[0]
            
            if count_antes > 0:
                print(f"🗑️ Eliminando {count_antes} contratos generados existentes (sin datos binarios)...")
                conn.execute(text("DELETE FROM contrato_generado;"))
                print("✅ Contratos existentes eliminados")
            
            # Confirmar cambios
            conn.commit()
            
            print("=" * 50)
            print("🎉 ¡Arreglo completado exitosamente!")
            print("📋 Resumen:")
            print(f"   - Columna archivo_data: ✅ Agregada/Verificada")
            print(f"   - Contratos antiguos eliminados: {count_antes}")
            print("   - Tabla lista para nuevos contratos con datos binarios")
            
            return True
            
    except Exception as e:
        print(f"❌ Error durante el arreglo: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Arreglador de Contratos Generados")
    print("=" * 50)
    
    if arreglar_contratos():
        print("\n✅ ¡Proceso completado exitosamente!")
        print("💡 Ahora puedes generar nuevos contratos que se guardarán correctamente.")
    else:
        print("\n❌ El proceso falló. Revisa los errores arriba.")
