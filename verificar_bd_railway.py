"""
Script para verificar la base de datos en Railway
"""

import os
import psycopg2
from datetime import datetime

def verificar_base_datos():
    print("🔍 VERIFICACIÓN DE BASE DE DATOS EN RAILWAY")
    print("=" * 50)
    
    # Obtener URL de la base de datos
    database_url = os.environ.get('DATABASE_PUBLIC_URL')
    if not database_url:
        print("❌ No se encontró DATABASE_PUBLIC_URL en las variables de entorno")
        return
    
    try:
        # Conectar a la base de datos
        print("🔌 Conectando a la base de datos...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        print("✅ Conexión exitosa")
        
        # Verificar tablas existentes
        print("\n📋 TABLAS EXISTENTES:")
        print("-" * 30)
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tablas = cursor.fetchall()
        
        for tabla in tablas:
            print(f"✅ {tabla[0]}")
        
        # Verificar tabla de notificaciones específicamente
        print("\n🔔 VERIFICACIÓN DE TABLA NOTIFICACIONES:")
        print("-" * 40)
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'notificacion'
            ORDER BY ordinal_position
        """)
        columnas = cursor.fetchall()
        
        if columnas:
            print("✅ Tabla 'notificacion' existe con las siguientes columnas:")
            for columna in columnas:
                print(f"   - {columna[0]}: {columna[1]} ({'NULL' if columna[2] == 'YES' else 'NOT NULL'})")
        else:
            print("❌ Tabla 'notificacion' NO existe")
        
        # Verificar categorías de inventario
        print("\n📂 VERIFICACIÓN DE CATEGORÍAS DE INVENTARIO:")
        print("-" * 45)
        cursor.execute("""
            SELECT id, nombre, descripcion, activa
            FROM categoria_inventario
            ORDER BY nombre
        """)
        categorias = cursor.fetchall()
        
        if categorias:
            print("✅ Categorías encontradas:")
            for categoria in categorias:
                estado = "Activa" if categoria[3] else "Inactiva"
                print(f"   - ID {categoria[0]}: {categoria[1]} ({estado})")
                if categoria[2]:
                    print(f"     Descripción: {categoria[2]}")
        else:
            print("❌ No se encontraron categorías de inventario")
        
        # Verificar notificaciones existentes
        print("\n🔔 VERIFICACIÓN DE NOTIFICACIONES:")
        print("-" * 35)
        cursor.execute("""
            SELECT COUNT(*) FROM notificacion
        """)
        count_notif = cursor.fetchone()[0]
        print(f"📊 Total de notificaciones: {count_notif}")
        
        if count_notif > 0:
            cursor.execute("""
                SELECT id, titulo, tipo, leida, fecha_creacion
                FROM notificacion
                ORDER BY fecha_creacion DESC
                LIMIT 5
            """)
            notificaciones = cursor.fetchall()
            print("📋 Últimas 5 notificaciones:")
            for notif in notificaciones:
                estado = "Leída" if notif[3] else "No leída"
                print(f"   - ID {notif[0]}: {notif[1]} ({notif[2]}) - {estado} - {notif[4]}")
        
        # Verificar productos de inventario
        print("\n📦 VERIFICACIÓN DE PRODUCTOS:")
        print("-" * 30)
        cursor.execute("""
            SELECT COUNT(*) FROM producto
        """)
        count_productos = cursor.fetchone()[0]
        print(f"📊 Total de productos: {count_productos}")
        
        # Verificar empleados
        print("\n👥 VERIFICACIÓN DE EMPLEADOS:")
        print("-" * 30)
        cursor.execute("""
            SELECT COUNT(*) FROM empleado
        """)
        count_empleados = cursor.fetchone()[0]
        print(f"📊 Total de empleados: {count_empleados}")
        
        # Verificar visitantes
        print("\n🚶 VERIFICACIÓN DE VISITANTES:")
        print("-" * 30)
        cursor.execute("""
            SELECT COUNT(*) FROM visitante
        """)
        count_visitantes = cursor.fetchone()[0]
        print(f"📊 Total de visitantes: {count_visitantes}")
        
        # Verificar asistencias
        print("\n⏰ VERIFICACIÓN DE ASISTENCIAS:")
        print("-" * 30)
        cursor.execute("""
            SELECT COUNT(*) FROM asistencia
        """)
        count_asistencias = cursor.fetchone()[0]
        print(f"📊 Total de asistencias: {count_asistencias}")
        
        cursor.close()
        conn.close()
        print("\n✅ Verificación completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_base_datos()
