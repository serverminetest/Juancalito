#!/usr/bin/env python3
"""
Script simple para probar la conexión a PostgreSQL
"""

import os
import psycopg2
from urllib.parse import urlparse

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
        # Parsear la URL
        parsed = urlparse(database_url)
        
        # Conectar usando psycopg2
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remover el '/' inicial
            user=parsed.username,
            password=parsed.password
        )
        
        # Probar la conexión
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Conexión exitosa a PostgreSQL: {version[:50]}...")
        
        # Cerrar la conexión
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
