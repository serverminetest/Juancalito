#!/usr/bin/env python3
"""
Script para crear las tablas usando los modelos de SQLAlchemy
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Importar los modelos de la aplicación
sys.path.append('.')
from app import app, db, User, Empleado, Asistencia, Visitante, ContactoEmergencia

def create_tables_from_models():
    """Crea las tablas usando los modelos de SQLAlchemy"""
    print("📊 Creando tablas usando modelos de SQLAlchemy...")
    
    # Obtener la URL de la base de datos
    database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL o DATABASE_PUBLIC_URL no configurada")
        return False
    
    try:
        # Configurar la aplicación con la URL de la base de datos
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        
        # Crear todas las tablas
        with app.app_context():
            db.create_all()
            print("✅ Tablas creadas exitosamente usando modelos de SQLAlchemy")
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
        
        # Configurar la aplicación
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        
        with app.app_context():
            # Verificar si ya existe el usuario admin
            existing_user = User.query.filter_by(email='admin@juancalito.com').first()
            if existing_user:
                print("✅ Usuario administrador ya existe")
                return True
            
            # Crear el usuario admin
            admin_user = User(
                email='admin@juancalito.com',
                username='Administrador',
                password_hash=generate_password_hash('nueva_contraseña_2024'),
                is_admin=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
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
    print("🚀 Creando tablas usando modelos de SQLAlchemy...")
    print("=" * 50)
    
    # Paso 1: Crear tablas
    if not create_tables_from_models():
        print("❌ No se pudieron crear las tablas")
        sys.exit(1)
    
    # Paso 2: Crear usuario admin
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
