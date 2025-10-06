#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar migración manual en Railway
Uso: railway run python railway_migrate.py
"""

import os
import sys
from sqlalchemy import create_engine, text

def main():
    """Ejecutar migración manual"""
    print("🚂 MIGRACIÓN MANUAL EN RAILWAY")
    print("=" * 50)
    
    # Obtener URL de la base de datos
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL no está configurada")
        print("💡 Asegúrate de estar ejecutando este script en Railway")
        sys.exit(1)
    
    print(f"📡 Conectando a la base de datos...")
    
    try:
        # Crear conexión
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Verificar conexión
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Conectado a PostgreSQL: {version[:50]}...")
            
            # Crear tablas de inventario
            tablas_sql = [
                """
                CREATE TABLE IF NOT EXISTS categoria_inventario (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL UNIQUE,
                    descripcion TEXT,
                    activa BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
                """
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
                """,
                """
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
            ]
            
            # Ejecutar creación de tablas
            for i, sql in enumerate(tablas_sql, 1):
                tabla_nombres = ['categoria_inventario', 'producto', 'movimiento_inventario']
                tabla_nombre = tabla_nombres[i-1]
                
                print(f"📝 Creando tabla {tabla_nombre}...")
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ Tabla {tabla_nombre} creada exitosamente")
            
            # Verificar columna archivo_data en contrato_generado
            print("📝 Verificando columna archivo_data...")
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'contrato_generado' AND column_name = 'archivo_data';
            """))
            
            if result.fetchone():
                print("✅ Columna archivo_data ya existe")
            else:
                print("🔨 Agregando columna archivo_data...")
                conn.execute(text("""
                    ALTER TABLE contrato_generado 
                    ADD COLUMN archivo_data BYTEA;
                """))
                conn.commit()
                print("✅ Columna archivo_data agregada")
            
            # Crear índices
            print("📝 Creando índices...")
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_producto_codigo ON producto(codigo);",
                "CREATE INDEX IF NOT EXISTS idx_producto_categoria ON producto(categoria_id);",
                "CREATE INDEX IF NOT EXISTS idx_movimiento_producto ON movimiento_inventario(producto_id);",
                "CREATE INDEX IF NOT EXISTS idx_movimiento_fecha ON movimiento_inventario(fecha_movimiento);"
            ]
            
            for indice in indices:
                try:
                    conn.execute(text(indice))
                    print("✅ Índice creado")
                except Exception as e:
                    print(f"⚠️ Índice: {str(e)[:50]}...")
            
            conn.commit()
            
            # Verificar tablas creadas
            print("\n📊 Verificando tablas...")
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('categoria_inventario', 'producto', 'movimiento_inventario')
                ORDER BY table_name;
            """))
            
            tablas_creadas = [row[0] for row in result.fetchall()]
            print(f"✅ Tablas disponibles: {', '.join(tablas_creadas)}")
            
            print("\n🎉 ¡Migración completada exitosamente!")
            print("🚀 El sistema de inventarios está listo para usar")
            
    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
