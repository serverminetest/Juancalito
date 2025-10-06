#!/usr/bin/env python3
"""
Script para reiniciar las secuencias de ID en Railway
Versión optimizada para Railway CLI
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def reset_sequences_railway():
    """Reinicia todas las secuencias de ID a 1 en Railway"""
    
    # Para Railway, usar DATABASE_PUBLIC_URL
    database_url = os.getenv('DATABASE_PUBLIC_URL')
    
    if not database_url:
        print("❌ Error: No se encontró DATABASE_PUBLIC_URL")
        print("💡 Asegúrate de ejecutar con: railway run python reset_sequences_railway.py")
        return False
    
    try:
        # Conectar a la base de datos
        print("🔗 Conectando a Railway PostgreSQL...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Lista de tablas y sus secuencias
        tables_sequences = [
            ('empleado', 'empleado_id_seq'),
            ('contrato', 'contrato_id_seq'),
            ('asistencia', 'asistencia_id_seq'),
            ('visitante', 'visitante_id_seq'),
            ('contrato_generado', 'contrato_generado_id_seq'),
            ('categoria_inventario', 'categoria_inventario_id_seq'),
            ('producto', 'producto_id_seq'),
            ('movimiento_inventario', 'movimiento_inventario_id_seq'),
        ]
        
        print("🔄 Reiniciando secuencias en Railway...")
        
        for table_name, sequence_name in tables_sequences:
            try:
                # Verificar si la tabla existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, (table_name,))
                
                table_exists = cursor.fetchone()[0]
                
                if table_exists:
                    # Verificar si la secuencia existe
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.sequences 
                            WHERE sequence_name = %s
                        );
                    """, (sequence_name,))
                    
                    sequence_exists = cursor.fetchone()[0]
                    
                    if sequence_exists:
                        # Obtener el máximo ID actual
                        cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name};")
                        max_id = cursor.fetchone()[0]
                        
                        if max_id > 0:
                            # Reiniciar la secuencia al siguiente valor después del máximo
                            next_val = max_id + 1
                            cursor.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH {next_val};")
                            print(f"✅ {table_name}: Secuencia reiniciada a {next_val}")
                        else:
                            # Si no hay registros, reiniciar a 1
                            cursor.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1;")
                            print(f"✅ {table_name}: Secuencia reiniciada a 1 (tabla vacía)")
                    else:
                        print(f"⚠️  {table_name}: Secuencia {sequence_name} no existe")
                else:
                    print(f"⚠️  {table_name}: Tabla no existe")
                    
            except Exception as e:
                print(f"❌ Error con {table_name}: {str(e)}")
        
        print("\n🎉 ¡Secuencias reiniciadas exitosamente en Railway!")
        print("\n📋 Resumen:")
        print("- Los nuevos empleados empezarán desde ID 1")
        print("- Los nuevos contratos empezarán desde ID 1")
        print("- Las nuevas asistencias empezarán desde ID 1")
        print("- Y así sucesivamente...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False

def main():
    print("🔄 REINICIO DE SECUENCIAS DE ID - RAILWAY")
    print("=" * 50)
    print("Este script reiniciará las secuencias de ID en Railway")
    print("para que los nuevos registros empiecen desde 1.")
    print()
    
    # Confirmación del usuario
    confirm = input("¿Estás seguro de que quieres continuar? (s/N): ").lower().strip()
    
    if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Operación cancelada.")
        return
    
    print()
    success = reset_sequences_railway()
    
    if success:
        print("\n✅ ¡Proceso completado exitosamente en Railway!")
    else:
        print("\n❌ El proceso falló. Revisa los errores arriba.")

if __name__ == "__main__":
    main()
