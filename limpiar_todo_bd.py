#!/usr/bin/env python3
"""
Script para limpiar TODOS los datos de la base de datos excepto usuarios
Mantiene solo: user
Elimina TODO lo demás: empleados, contratos, asistencias, visitantes, inventario, notificaciones
"""

from app import app, db
from sqlalchemy import text

def limpiar_todo_base_datos():
    """Limpiar TODA la base de datos manteniendo solo usuarios"""
    
    with app.app_context():
        print("=" * 70)
        print("🧹 LIMPIANDO TODA LA BASE DE DATOS")
        print("=" * 70)
        print("📋 Manteniendo SOLO:")
        print("   - user (usuarios)")
        print("=" * 70)
        print("🗑️ Eliminando TODO:")
        print("   - empleado")
        print("   - contrato") 
        print("   - asistencia")
        print("   - visitante")
        print("   - notificacion")
        print("   - categoria_inventario")
        print("   - producto")
        print("   - movimiento_inventario")
        print("   - contrato_generado")
        print("=" * 70)
        
        try:
            # Lista de tablas a eliminar (TODO excepto user)
            tablas_a_eliminar = [
                'asistencia',
                'visitante', 
                'notificacion',
                'categoria_inventario',
                'producto',
                'movimiento_inventario',
                'contrato_generado',
                'contrato',
                'empleado'
            ]
            
            print("🗑️ Eliminando tablas...")
            for tabla in tablas_a_eliminar:
                try:
                    with db.engine.connect() as conn:
                        # Verificar si la tabla existe
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
            
            # Regenerar secuencia solo para user
            try:
                with db.engine.connect() as conn:
                    # Obtener el máximo ID actual de user
                    result = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM \"user\";"))
                    max_id = result.fetchone()[0]
                    
                    # Resetear secuencia
                    if max_id > 0:
                        conn.execute(text(f"ALTER SEQUENCE user_id_seq RESTART WITH {max_id + 1};"))
                        conn.commit()
                        print(f"   ✅ Secuencia user_id_seq reiniciada en {max_id + 1}")
                    else:
                        conn.execute(text("ALTER SEQUENCE user_id_seq RESTART WITH 1;"))
                        conn.commit()
                        print(f"   ✅ Secuencia user_id_seq reiniciada en 1")
                        
            except Exception as e:
                print(f"   ⚠️ Error con secuencia user_id_seq: {e}")
            
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
            
            print("\n" + "=" * 70)
            print("🎉 LIMPIEZA COMPLETA EXITOSA")
            print("=" * 70)
            print("📋 Resumen:")
            print(f"   - Tablas eliminadas: {len(tablas_a_eliminar)}")
            print(f"   - Tablas restantes: {len(tablas_restantes)}")
            print("   - Solo usuarios mantenidos: ✅")
            print("   - Secuencias regeneradas: ✅")
            print("=" * 70)
            print("⚠️ IMPORTANTE:")
            print("   - Todos los empleados fueron eliminados")
            print("   - Todos los contratos fueron eliminados")
            print("   - Todas las asistencias fueron eliminadas")
            print("   - Todos los visitantes fueron eliminados")
            print("   - Todo el inventario fue eliminado")
            print("   - Todas las notificaciones fueron eliminadas")
            print("   - Solo los usuarios administradores quedaron")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"❌ Error durante la limpieza: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("⚠️ ADVERTENCIA CRÍTICA: Este script eliminará TODOS los datos excepto usuarios!")
    print("⚠️ Se eliminarán: empleados, contratos, asistencias, visitantes, inventario, etc.")
    print("⚠️ Solo se mantendrán los usuarios administradores.")
    print("\n¿Estás ABSOLUTAMENTE seguro de que quieres continuar? (escribir 'SI' para confirmar): ", end="")
    
    respuesta = input().strip()
    
    if respuesta == 'SI':
        limpiar_todo_base_datos()
    else:
        print("❌ Operación cancelada por el usuario")
