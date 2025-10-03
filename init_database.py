#!/usr/bin/env python3
"""
Script para inicializar la base de datos PostgreSQL en Railway
Este script se conecta directamente a la base de datos y crea las tablas necesarias
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("🔍 Probando conexión a la base de datos...")
    
    # Obtener la URL de la base de datos (usar pública para scripts)
    database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL o DATABASE_PUBLIC_URL no configurada")
        return False
    
    print(f"📡 URL de conexión: {database_url[:50]}...")
    
    try:
        # Crear el motor de SQLAlchemy
        engine = create_engine(database_url)
        
        # Probar la conexión
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Conexión exitosa a PostgreSQL: {version[:50]}...")
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def create_tables():
    """Crea las tablas necesarias en la base de datos"""
    print("📊 Creando tablas en la base de datos...")
    
    database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL o DATABASE_PUBLIC_URL no configurada")
        return False
    
    try:
        # Crear el motor de SQLAlchemy
        engine = create_engine(database_url)
        
        # Definir las tablas
        tables_sql = """
        -- Tabla de usuarios
        CREATE TABLE IF NOT EXISTS "user" (
            id SERIAL PRIMARY KEY,
            email VARCHAR(120) UNIQUE NOT NULL,
            username VARCHAR(80) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabla de empleados
        CREATE TABLE IF NOT EXISTS empleado (
            id SERIAL PRIMARY KEY,
            nombre_completo VARCHAR(100) NOT NULL,
            documento VARCHAR(20) UNIQUE NOT NULL,
            cargo VARCHAR(50) NOT NULL,
            salario DECIMAL(10,2) NOT NULL,
            fecha_ingreso DATE NOT NULL,
            activo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabla de asistencias
        CREATE TABLE IF NOT EXISTS asistencia (
            id SERIAL PRIMARY KEY,
            empleado_id INTEGER NOT NULL REFERENCES empleado(id),
            fecha DATE NOT NULL,
            hora_entrada TIME,
            hora_salida TIME,
            horas_trabajadas DECIMAL(4,2),
            observaciones TEXT,
            token_diario VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabla de visitantes
        CREATE TABLE IF NOT EXISTS visitante (
            id SERIAL PRIMARY KEY,
            nombre_completo VARCHAR(100) NOT NULL,
            documento VARCHAR(20) NOT NULL,
            telefono VARCHAR(15),
            empresa VARCHAR(100),
            motivo_visita TEXT NOT NULL,
            persona_visita VARCHAR(100) NOT NULL,
            fecha_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_salida TIMESTAMP,
            estado VARCHAR(20) DEFAULT 'Dentro',
            observaciones TEXT,
            token_diario VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabla de contactos de emergencia
        CREATE TABLE IF NOT EXISTS contacto_emergencia (
            id SERIAL PRIMARY KEY,
            visitante_id INTEGER NOT NULL REFERENCES visitante(id),
            nombre VARCHAR(100) NOT NULL,
            telefono VARCHAR(15) NOT NULL,
            parentesco VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Ejecutar las consultas
        with engine.connect() as connection:
            # Dividir las consultas por ';' y ejecutarlas una por una
            for query in tables_sql.split(';'):
                query = query.strip()
                if query:
                    connection.execute(text(query))
            
            connection.commit()
            print("✅ Tablas creadas exitosamente")
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Error al crear tablas: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def create_admin_user():
    """Crea el usuario administrador por defecto"""
    print("👤 Creando usuario administrador...")
    
    database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL o DATABASE_PUBLIC_URL no configurada")
        return False
    
    try:
        from werkzeug.security import generate_password_hash
        
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Verificar si ya existe el usuario admin
            result = connection.execute(text("SELECT id FROM \"user\" WHERE email = 'admin@juancalito.com'"))
            if result.fetchone():
                print("✅ Usuario administrador ya existe")
                return True
            
            # Crear el usuario admin
            password_hash = generate_password_hash('nueva_contraseña_2024')
            connection.execute(text("""
                INSERT INTO "user" (email, username, password_hash, is_admin) 
                VALUES ('admin@juancalito.com', 'Administrador', :password_hash, true)
            """), {"password_hash": password_hash})
            
            connection.commit()
            print("✅ Usuario administrador creado: admin@juancalito.com / nueva_contraseña_2024")
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Error al crear usuario admin: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🚀 Inicializando base de datos PostgreSQL...")
    print("=" * 50)
    
    # Paso 1: Probar conexión
    if not test_database_connection():
        print("❌ No se pudo conectar a la base de datos")
        sys.exit(1)
    
    # Paso 2: Crear tablas
    if not create_tables():
        print("❌ No se pudieron crear las tablas")
        sys.exit(1)
    
    # Paso 3: Crear usuario admin
    if not create_admin_user():
        print("❌ No se pudo crear el usuario administrador")
        sys.exit(1)
    
    print("=" * 50)
    print("🎉 ¡Base de datos inicializada correctamente!")
    print("📱 Credenciales de acceso:")
    print("   Email: admin@juancalito.com")
    print("   Contraseña: nueva_contraseña_2024")

if __name__ == "__main__":
    main()
