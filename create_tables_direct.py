#!/usr/bin/env python3
"""
Script directo para crear las tablas usando la URL pública
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def create_tables_direct():
    """Crea las tablas directamente usando SQL"""
    print("🚀 Creando tablas directamente en PostgreSQL...")
    print("=" * 50)
    
    # Usar SOLO la URL pública
    database_url = os.environ.get('DATABASE_PUBLIC_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_PUBLIC_URL no configurada")
        return False
    
    print(f"📡 Usando URL pública: {database_url[:50]}...")
    
    try:
        # Crear el motor de SQLAlchemy
        engine = create_engine(database_url)
        
        # Definir las tablas con la estructura correcta
        tables_sql = """
        -- Eliminar tablas existentes si existen
        DROP TABLE IF EXISTS contacto_emergencia CASCADE;
        DROP TABLE IF EXISTS asistencia CASCADE;
        DROP TABLE IF EXISTS contrato CASCADE;
        DROP TABLE IF EXISTS visitante CASCADE;
        DROP TABLE IF EXISTS empleado CASCADE;
        DROP TABLE IF EXISTS "user" CASCADE;
        
        -- Tabla de usuarios
        CREATE TABLE "user" (
            id SERIAL PRIMARY KEY,
            email VARCHAR(120) UNIQUE NOT NULL,
            username VARCHAR(80) NOT NULL,
            password_hash VARCHAR(120) NOT NULL,
            is_admin BOOLEAN DEFAULT TRUE
        );
        
        -- Tabla de empleados (con todas las columnas del modelo)
        CREATE TABLE empleado (
            id SERIAL PRIMARY KEY,
            nombre_completo VARCHAR(200) NOT NULL,
            cedula VARCHAR(20) UNIQUE NOT NULL,
            fecha_nacimiento DATE NOT NULL,
            genero VARCHAR(20) NOT NULL,
            estado_civil VARCHAR(30) NOT NULL,
            telefono_principal VARCHAR(20) NOT NULL,
            telefono_secundario VARCHAR(20),
            email_personal VARCHAR(120) NOT NULL,
            email_corporativo VARCHAR(120),
            direccion_residencia TEXT NOT NULL,
            ciudad VARCHAR(100) NOT NULL,
            departamento VARCHAR(100) NOT NULL,
            codigo_postal VARCHAR(10),
            cargo_puesto VARCHAR(100) NOT NULL,
            departamento_laboral VARCHAR(50) NOT NULL,
            fecha_ingreso DATE NOT NULL,
            tipo_contrato VARCHAR(30) NOT NULL,
            salario_base FLOAT NOT NULL,
            tipo_salario VARCHAR(20) NOT NULL,
            jornada_laboral VARCHAR(30) NOT NULL,
            ubicacion_trabajo VARCHAR(20) NOT NULL,
            estado_empleado VARCHAR(20) NOT NULL DEFAULT 'Activo',
            supervisor VARCHAR(100),
            horario VARCHAR(100),
            eps VARCHAR(100) NOT NULL,
            arl VARCHAR(100) NOT NULL,
            afp VARCHAR(100) NOT NULL,
            caja_compensacion VARCHAR(100),
            nombre_contacto_emergencia VARCHAR(200) NOT NULL,
            telefono_emergencia VARCHAR(20) NOT NULL,
            parentesco VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabla de contratos
        CREATE TABLE contrato (
            id SERIAL PRIMARY KEY,
            empleado_id INTEGER NOT NULL REFERENCES empleado(id),
            tipo_contrato VARCHAR(50) NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE,
            salario FLOAT NOT NULL,
            descripcion TEXT,
            activo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabla de contratos generados
        CREATE TABLE contrato_generado (
            id SERIAL PRIMARY KEY,
            empleado_id INTEGER NOT NULL REFERENCES empleado(id),
            contrato_id INTEGER NOT NULL REFERENCES contrato(id),
            nombre_archivo VARCHAR(255) NOT NULL,
            ruta_archivo VARCHAR(500) NOT NULL,
            archivo_data BYTEA,
            fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activo BOOLEAN DEFAULT TRUE
        );
        
        -- Tabla de asistencias
        CREATE TABLE asistencia (
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
        
        -- Tabla de visitantes (con la estructura correcta del modelo)
        CREATE TABLE visitante (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            documento VARCHAR(20) NOT NULL,
            eps VARCHAR(100) NOT NULL,
            rh VARCHAR(10) NOT NULL,
            telefono VARCHAR(20) NOT NULL,
            empresa VARCHAR(100),
            motivo_visita TEXT NOT NULL,
            fecha_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_salida TIMESTAMP,
            estado_visita VARCHAR(20) DEFAULT 'En visita',
            nombre_contacto_emergencia VARCHAR(200) NOT NULL,
            telefono_emergencia VARCHAR(20) NOT NULL,
            parentesco VARCHAR(50) NOT NULL,
            activo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabla de contactos de emergencia
        CREATE TABLE contacto_emergencia (
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
            
            # Crear usuario administrador
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash('nueva_contraseña_2024')
            
            connection.execute(text("""
                INSERT INTO "user" (email, username, password_hash, is_admin) 
                VALUES ('admin@juancalito.com', 'Administrador', :password_hash, true)
                ON CONFLICT (email) DO NOTHING
            """), {"password_hash": password_hash})
            
            connection.commit()
            print("✅ Usuario administrador creado: admin@juancalito.com / nueva_contraseña_2024")
            
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Error al crear tablas: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def main():
    """Función principal"""
    if create_tables_direct():
        print("=" * 50)
        print("🎉 ¡Base de datos inicializada correctamente!")
        print("📱 Credenciales de acceso:")
        print("   Email: admin@juancalito.com")
        print("   Contraseña: nueva_contraseña_2024")
    else:
        print("❌ Error al inicializar la base de datos")
        sys.exit(1)

if __name__ == "__main__":
    main()
