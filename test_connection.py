#!/usr/bin/env python3
"""
Script simple para probar la conexión a PostgreSQL
"""

import os
from sqlalchemy import create_engine, text

def test_connection():
    """Prueba la conexión directa a PostgreSQL"""
    print("🔍 Probando conexión directa a PostgreSQL...")
    
    # Obtener la URL de la base de datos
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL no configurada")
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
        
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
