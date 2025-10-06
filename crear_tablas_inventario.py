#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear tablas de inventario manualmente
"""

import os
import sys
from sqlalchemy import create_engine, text

def crear_tablas_inventario():
    """Crear tablas de inventario manualmente"""
    print("🚀 CREANDO TABLAS DE INVENTARIO MANUALMENTE")
    print("=" * 60)
    
    # Obtener URL de la base de datos (usar URL pública para CLI)
    database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL o DATABASE_PUBLIC_URL no está configurada")
        return False
    
    print(f"📡 Usando URL: {database_url[:50]}...")
    
    try:
        # Crear conexión
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Verificar conexión
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Conectado a PostgreSQL: {version[:50]}...")
            
            # Crear tablas de inventario
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
            
            for tabla in tablas_inventario:
                print(f"📝 Creando tabla {tabla['nombre']}...")
                try:
                    conn.execute(text(tabla['sql']))
                    conn.commit()
                    print(f"✅ Tabla {tabla['nombre']} creada exitosamente")
                except Exception as e:
                    print(f"❌ Error con tabla {tabla['nombre']}: {str(e)}")
                    return False
            
            # Verificar columna archivo_data en contrato_generado
            print("📝 Verificando columna archivo_data...")
            try:
                conn.execute(text("""
                    ALTER TABLE contrato_generado 
                    ADD COLUMN IF NOT EXISTS archivo_data BYTEA;
                """))
                conn.commit()
                print("✅ Columna archivo_data verificada")
            except Exception as e:
                print(f"⚠️ Columna archivo_data: {str(e)}")
            
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
            print(f"✅ Tablas disponibles: {', '.join(tablas_creadas)}")
            
            print("\n🎉 ¡Tablas de inventario creadas exitosamente!")
            return True
            
    except Exception as e:
        print(f"❌ Error durante la creación: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🔄 CREACIÓN MANUAL DE TABLAS DE INVENTARIO")
    print("=" * 60)
    
    success = crear_tablas_inventario()
    
    if success:
        print("\n✅ ¡Proceso completado exitosamente!")
        print("🚀 El sistema de inventarios está listo para usar")
        sys.exit(0)
    else:
        print("\n❌ Proceso falló - Revisar logs para más detalles")
        sys.exit(1)

if __name__ == "__main__":
    main()
