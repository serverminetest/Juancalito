#!/usr/bin/env python3
"""
Script para limpiar la base de datos
Mantiene solo: empleado, contrato, user
Elimina todo lo demás y regenera secuencias
"""

from app import app, db
from sqlalchemy import text

def limpiar_base_datos():
    """Limpiar base de datos manteniendo solo tablas esenciales"""
    
    with app.app_context():
        print("=" * 60)
        print("🧹 LIMPIANDO BASE DE DATOS")
        print("=" * 60)
        print("📋 Manteniendo tablas:")
        print("   - user (usuarios)")
        print("   - empleado")
        print("   - contrato")
        print("=" * 60)
        
        try:
            # Lista de tablas a eliminar
            tablas_a_eliminar = [
                'asistencia',
                'visitante', 
                'notificacion',
                'categoria_inventario',
                'producto',
                'movimiento_inventario',
                'contrato_generado'
            ]
            
            print("🗑️ Eliminando tablas...")
            for tabla in tablas_a_eliminar:
                try:
                    # Verificar si la tabla existe
                    with db.engine.connect() as conn:
                        result = conn.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = '{tabla}'
                            );
                        """))
                        existe = result.fetchone()[0]
                        
                        if existe:
                            print(f"   ❌ Eliminando tabla: {tabla}")
                            conn.execute(text(f"DROP TABLE IF EXISTS {tabla} CASCADE;"))
                            conn.commit()
                            print(f"   ✅ Tabla {tabla} eliminada")
                        else:
                            print(f"   ⚠️ Tabla {tabla} no existe, saltando...")
                        
                except Exception as e:
                    print(f"   ⚠️ Error eliminando {tabla}: {e}")
            
            print("\n🔄 Regenerando secuencias...")
            
            # Regenerar secuencias para las tablas que mantenemos
            secuencias = [
                ('user', 'id'),
                ('empleado', 'id'), 
                ('contrato', 'id')
            ]
            
            for tabla, columna in secuencias:
                try:
                    with db.engine.connect() as conn:
                        # Obtener el máximo ID actual
                        result = conn.execute(text(f"SELECT COALESCE(MAX({columna}), 0) FROM {tabla};"))
                        max_id = result.fetchone()[0]
                        
                        # Resetear secuencia
                        if max_id > 0:
                            conn.execute(text(f"ALTER SEQUENCE {tabla}_{columna}_seq RESTART WITH {max_id + 1};"))
                            conn.commit()
                            print(f"   ✅ Secuencia {tabla}_{columna}_seq reiniciada en {max_id + 1}")
                        else:
                            conn.execute(text(f"ALTER SEQUENCE {tabla}_{columna}_seq RESTART WITH 1;"))
                            conn.commit()
                            print(f"   ✅ Secuencia {tabla}_{columna}_seq reiniciada en 1")
                            
                except Exception as e:
                    print(f"   ⚠️ Error con secuencia {tabla}_{columna}_seq: {e}")
            
            # Commit todos los cambios
            db.session.commit()
            
            print("\n📊 Verificando tablas restantes...")
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """))
                
                tablas_restantes = [row[0] for row in result.fetchall()]
            print("✅ Tablas restantes:")
            for tabla in tablas_restantes:
                print(f"   - {tabla}")
            
            print("\n" + "=" * 60)
            print("🎉 LIMPIEZA COMPLETADA EXITOSAMENTE")
            print("=" * 60)
            print("📋 Resumen:")
            print(f"   - Tablas eliminadas: {len(tablas_a_eliminar)}")
            print(f"   - Tablas restantes: {len(tablas_restantes)}")
            print("   - Secuencias regeneradas: ✅")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Error durante la limpieza: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("⚠️ ADVERTENCIA: Este script eliminará datos permanentemente!")
    print("¿Estás seguro de que quieres continuar? (s/N): ", end="")
    
    respuesta = input().lower().strip()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        limpiar_base_datos()
    else:
        print("❌ Operación cancelada por el usuario")
