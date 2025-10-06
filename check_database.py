#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el estado de la base de datos
"""

import os
import sys
from sqlalchemy import create_engine, text

def check_database():
    """Verificar el estado de la base de datos"""
    print("🔍 VERIFICACIÓN DE BASE DE DATOS")
    print("=" * 50)
    
    # Obtener URL de la base de datos
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL no está configurada")
        sys.exit(1)
    
    try:
        # Crear conexión
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Verificar conexión
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Conectado a PostgreSQL: {version[:50]}...")
            
            # Verificar tablas principales
            print("\n📊 Verificando tablas principales...")
            tablas_principales = [
                'user', 'empleado', 'contrato', 'asistencia', 'visitante'
            ]
            
            for tabla in tablas_principales:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {tabla};"))
                    count = result.fetchone()[0]
                    print(f"   ✅ {tabla}: {count} registros")
                except Exception as e:
                    print(f"   ❌ {tabla}: Error - {str(e)[:50]}...")
            
            # Verificar tablas de inventario
            print("\n📦 Verificando tablas de inventario...")
            tablas_inventario = [
                'categoria_inventario', 'producto', 'movimiento_inventario'
            ]
            
            for tabla in tablas_inventario:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {tabla};"))
                    count = result.fetchone()[0]
                    print(f"   ✅ {tabla}: {count} registros")
                except Exception as e:
                    print(f"   ❌ {tabla}: No existe - {str(e)[:50]}...")
            
            # Verificar tabla contrato_generado
            print("\n📄 Verificando tabla contrato_generado...")
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM contrato_generado;"))
                count = result.fetchone()[0]
                print(f"   ✅ contrato_generado: {count} registros")
                
                # Verificar columna archivo_data
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'contrato_generado' AND column_name = 'archivo_data';
                """))
                
                if result.fetchone():
                    print("   ✅ Columna archivo_data: Existe")
                else:
                    print("   ❌ Columna archivo_data: No existe")
                    
            except Exception as e:
                print(f"   ❌ contrato_generado: Error - {str(e)[:50]}...")
            
            # Verificar índices
            print("\n🔍 Verificando índices...")
            try:
                result = conn.execute(text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename IN ('producto', 'movimiento_inventario')
                    ORDER BY tablename, indexname;
                """))
                
                indices = [row[0] for row in result.fetchall()]
                if indices:
                    print(f"   ✅ Índices encontrados: {len(indices)}")
                    for indice in indices:
                        print(f"      - {indice}")
                else:
                    print("   ⚠️ No se encontraron índices específicos")
                    
            except Exception as e:
                print(f"   ❌ Error verificando índices: {str(e)[:50]}...")
            
            # Resumen final
            print("\n📈 RESUMEN:")
            print("=" * 50)
            
            # Contar todas las tablas
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public';
            """))
            total_tablas = result.fetchone()[0]
            print(f"📊 Total de tablas: {total_tablas}")
            
            # Verificar si el sistema de inventarios está listo
            tablas_inventario_ok = 0
            for tabla in tablas_inventario:
                try:
                    conn.execute(text(f"SELECT 1 FROM {tabla} LIMIT 1;"))
                    tablas_inventario_ok += 1
                except:
                    pass
            
            if tablas_inventario_ok == len(tablas_inventario):
                print("🎉 Sistema de inventarios: ✅ LISTO")
            else:
                print(f"⚠️ Sistema de inventarios: {tablas_inventario_ok}/{len(tablas_inventario)} tablas")
            
            print("\n💡 Para migrar la base de datos, ejecuta:")
            print("   railway run python railway_migrate.py")
            
    except Exception as e:
        print(f"❌ Error verificando base de datos: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    check_database()
