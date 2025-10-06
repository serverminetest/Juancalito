#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración automática para Railway
Actualiza la base de datos con las nuevas tablas de inventarios
"""

import os
import sys
from sqlalchemy import create_engine, text
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_database_url():
    """Obtiene la URL de la base de datos"""
    # En Railway, usar la URL interna para la aplicación
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL no está configurada")
        sys.exit(1)
    return database_url

def migrate_database():
    """Ejecuta la migración de la base de datos"""
    print("🚀 Iniciando migración de base de datos...")
    print("=" * 60)
    
    try:
        # Obtener URL de la base de datos
        database_url = get_database_url()
        print(f"📡 Conectando a la base de datos...")
        
        # Crear conexión
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Verificar conexión
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Conectado a PostgreSQL: {version[:50]}...")
            
            # Lista de tablas a crear/verificar
            tablas_inventario = [
                {
                    'nombre': 'categoria_inventario',
                    'sql': """
                        CREATE TABLE IF NOT EXISTS categoria_inventario (
                            id SERIAL PRIMARY KEY,
                            nombre VARCHAR(100) NOT NULL UNIQUE,
                            descripcion TEXT,
                            activa BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """
                },
                {
                    'nombre': 'producto',
                    'sql': """
                        CREATE TABLE IF NOT EXISTS producto (
                            id SERIAL PRIMARY KEY,
                            codigo VARCHAR(50) NOT NULL UNIQUE,
                            nombre VARCHAR(200) NOT NULL,
                            descripcion TEXT,
                            categoria_id INTEGER NOT NULL REFERENCES categoria_inventario(id),
                            unidad_medida VARCHAR(20) NOT NULL,
                            precio_unitario NUMERIC(10, 2) DEFAULT 0,
                            stock_minimo INTEGER DEFAULT 0,
                            stock_actual INTEGER DEFAULT 0,
                            ubicacion VARCHAR(100),
                            proveedor VARCHAR(200),
                            fecha_vencimiento DATE,
                            lote VARCHAR(50),
                            activo BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """
                },
                {
                    'nombre': 'movimiento_inventario',
                    'sql': """
                        CREATE TABLE IF NOT EXISTS movimiento_inventario (
                            id SERIAL PRIMARY KEY,
                            producto_id INTEGER NOT NULL REFERENCES producto(id),
                            tipo_movimiento VARCHAR(20) NOT NULL,
                            cantidad INTEGER NOT NULL,
                            precio_unitario NUMERIC(10, 2),
                            total NUMERIC(10, 2),
                            motivo VARCHAR(200),
                            referencia VARCHAR(100),
                            responsable VARCHAR(200),
                            observaciones TEXT,
                            fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            created_by INTEGER REFERENCES "user"(id)
                        );
                    """
                }
            ]
            
            # Verificar y crear tablas de inventario
            for tabla in tablas_inventario:
                print(f"📝 Verificando tabla {tabla['nombre']}...")
                
                # Verificar si la tabla existe
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = :tabla_nombre
                    );
                """), {'tabla_nombre': tabla['nombre']})
                
                tabla_existe = result.fetchone()[0]
                
                if tabla_existe:
                    print(f"✅ Tabla {tabla['nombre']} ya existe")
                else:
                    print(f"🔨 Creando tabla {tabla['nombre']}...")
                    conn.execute(text(tabla['sql']))
                    conn.commit()
                    print(f"✅ Tabla {tabla['nombre']} creada exitosamente")
            
            # Verificar columna archivo_data en contrato_generado
            print("📝 Verificando columna archivo_data en contrato_generado...")
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'contrato_generado' AND column_name = 'archivo_data';
            """))
            
            if result.fetchone():
                print("✅ Columna archivo_data ya existe en contrato_generado")
            else:
                print("🔨 Agregando columna archivo_data a contrato_generado...")
                conn.execute(text("""
                    ALTER TABLE contrato_generado 
                    ADD COLUMN archivo_data BYTEA;
                """))
                conn.commit()
                print("✅ Columna archivo_data agregada exitosamente")
            
            # Crear índices para mejorar rendimiento
            print("📝 Creando índices para mejorar rendimiento...")
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_producto_codigo ON producto(codigo);",
                "CREATE INDEX IF NOT EXISTS idx_producto_categoria ON producto(categoria_id);",
                "CREATE INDEX IF NOT EXISTS idx_movimiento_producto ON movimiento_inventario(producto_id);",
                "CREATE INDEX IF NOT EXISTS idx_movimiento_fecha ON movimiento_inventario(fecha_movimiento);",
                "CREATE INDEX IF NOT EXISTS idx_movimiento_tipo ON movimiento_inventario(tipo_movimiento);"
            ]
            
            for indice in indices:
                try:
                    conn.execute(text(indice))
                    print(f"✅ Índice creado")
                except Exception as e:
                    print(f"⚠️ Índice ya existe o error: {str(e)[:50]}...")
            
            conn.commit()
            
            # Verificar tablas creadas
            print("\n📊 Verificando tablas creadas...")
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('categoria_inventario', 'producto', 'movimiento_inventario')
                ORDER BY table_name;
            """))
            
            tablas_creadas = [row[0] for row in result.fetchall()]
            print(f"✅ Tablas de inventario disponibles: {', '.join(tablas_creadas)}")
            
            # Estadísticas finales
            print("\n📈 Estadísticas de la base de datos:")
            for tabla in ['user', 'empleado', 'contrato', 'categoria_inventario', 'producto', 'movimiento_inventario']:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {tabla};"))
                    count = result.fetchone()[0]
                    print(f"   {tabla}: {count} registros")
                except Exception as e:
                    print(f"   {tabla}: No disponible")
            
            print("\n🎉 ¡Migración completada exitosamente!")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🔄 MIGRACIÓN AUTOMÁTICA DE BASE DE DATOS")
    print("=" * 60)
    print("Este script actualiza la base de datos con las nuevas tablas de inventarios")
    print("=" * 60)
    
    # Verificar si estamos en Railway
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        print("🚂 Detectado entorno Railway")
    else:
        print("💻 Ejecutándose en entorno local")
    
    # Ejecutar migración
    success = migrate_database()
    
    if success:
        print("\n✅ Migración exitosa - La base de datos está lista para el sistema de inventarios")
        sys.exit(0)
    else:
        print("\n❌ Migración fallida - Revisar logs para más detalles")
        sys.exit(1)

if __name__ == "__main__":
    main()
