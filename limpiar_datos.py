#!/usr/bin/env python3
"""
Script para limpiar todos los datos de la aplicación
Mantiene solo el usuario administrador
"""

import os
import sys
from datetime import datetime

# Agregar el directorio actual al path para importar app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def limpiar_datos():
    """Limpiar todos los datos excepto el usuario administrador"""
    
    print("🧹 LIMPIANDO DATOS DE LA APLICACIÓN")
    print("=" * 60)
    
    try:
        # Importar la aplicación
        from app import app, db
        from app import (
            User, Empleado, Asistencia, Visitante, 
            Contrato, ContratoGenerado,
            CategoriaInventario, Producto, MovimientoInventario
        )
        
        with app.app_context():
            print("📊 Conectando a la base de datos...")
            
            # Confirmar acción
            print("\n⚠️  ADVERTENCIA: Este script eliminará TODOS los datos excepto el usuario administrador")
            print("📋 Datos que se eliminarán:")
            print("   • Empleados")
            print("   • Asistencias")
            print("   • Visitantes")
            print("   • Contratos y contratos generados")
            print("   • Categorías de inventario")
            print("   • Productos de inventario")
            print("   • Movimientos de inventario")
            print("\n✅ Datos que se mantendrán:")
            print("   • Usuario administrador")
            
            respuesta = input("\n¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
            
            if respuesta != 'SI':
                print("❌ Operación cancelada por el usuario")
                return
            
            print("\n🗑️  Iniciando limpieza de datos...")
            
            # Contar registros antes de eliminar
            empleados_count = Empleado.query.count()
            asistencias_count = Asistencia.query.count()
            visitantes_count = Visitante.query.count()
            contratos_count = Contrato.query.count()
            contratos_generados_count = ContratoGenerado.query.count()
            categorias_count = CategoriaInventario.query.count()
            productos_count = Producto.query.count()
            movimientos_count = MovimientoInventario.query.count()
            
            print(f"📊 Registros encontrados:")
            print(f"   • Empleados: {empleados_count}")
            print(f"   • Asistencias: {asistencias_count}")
            print(f"   • Visitantes: {visitantes_count}")
            print(f"   • Contratos: {contratos_count}")
            print(f"   • Contratos generados: {contratos_generados_count}")
            print(f"   • Categorías: {categorias_count}")
            print(f"   • Productos: {productos_count}")
            print(f"   • Movimientos: {movimientos_count}")
            
            # Eliminar datos en orden correcto (respetando foreign keys)
            print("\n🗑️  Eliminando datos...")
            
            # 1. Eliminar movimientos de inventario
            if movimientos_count > 0:
                print("   • Eliminando movimientos de inventario...")
                MovimientoInventario.query.delete()
                print(f"   ✅ {movimientos_count} movimientos eliminados")
            
            # 2. Eliminar productos
            if productos_count > 0:
                print("   • Eliminando productos...")
                Producto.query.delete()
                print(f"   ✅ {productos_count} productos eliminados")
            
            # 3. Eliminar categorías de inventario
            if categorias_count > 0:
                print("   • Eliminando categorías de inventario...")
                CategoriaInventario.query.delete()
                print(f"   ✅ {categorias_count} categorías eliminadas")
            
            # 4. Eliminar contratos generados
            if contratos_generados_count > 0:
                print("   • Eliminando contratos generados...")
                ContratoGenerado.query.delete()
                print(f"   ✅ {contratos_generados_count} contratos generados eliminados")
            
            # 5. Eliminar contratos
            if contratos_count > 0:
                print("   • Eliminando contratos...")
                Contrato.query.delete()
                print(f"   ✅ {contratos_count} contratos eliminados")
            
            # 6. Eliminar asistencias
            if asistencias_count > 0:
                print("   • Eliminando asistencias...")
                Asistencia.query.delete()
                print(f"   ✅ {asistencias_count} asistencias eliminadas")
            
            # 7. Eliminar visitantes
            if visitantes_count > 0:
                print("   • Eliminando visitantes...")
                Visitante.query.delete()
                print(f"   ✅ {visitantes_count} visitantes eliminados")
            
            # 8. Eliminar empleados
            if empleados_count > 0:
                print("   • Eliminando empleados...")
                Empleado.query.delete()
                print(f"   ✅ {empleados_count} empleados eliminados")
            
            # Confirmar cambios
            db.session.commit()
            
            print("\n✅ Limpieza completada exitosamente!")
            print("=" * 60)
            
            # Verificar que solo queda el administrador
            usuarios_count = User.query.count()
            admin_user = User.query.filter_by(is_admin=True).first()
            
            print(f"👤 Usuarios restantes: {usuarios_count}")
            if admin_user:
                print(f"   • Administrador: {admin_user.email}")
            
            print("\n🎯 La aplicación está lista para datos reales!")
            print("📝 Próximos pasos recomendados:")
            print("   1. Crear empleados")
            print("   2. Crear categorías de inventario")
            print("   3. Importar productos desde Excel")
            print("   4. Configurar contratos")
            
    except Exception as e:
        print(f"\n❌ Error durante la limpieza: {str(e)}")
        print("🔄 Reintentando...")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def verificar_estado():
    """Verificar el estado actual de la base de datos"""
    
    print("📊 VERIFICANDO ESTADO DE LA BASE DE DATOS")
    print("=" * 60)
    
    try:
        from app import app, db
        from app import (
            User, Empleado, Asistencia, Visitante, 
            Contrato, ContratoGenerado,
            CategoriaInventario, Producto, MovimientoInventario
        )
        
        with app.app_context():
            # Contar registros
            usuarios_count = User.query.count()
            empleados_count = Empleado.query.count()
            asistencias_count = Asistencia.query.count()
            visitantes_count = Visitante.query.count()
            contratos_count = Contrato.query.count()
            contratos_generados_count = ContratoGenerado.query.count()
            categorias_count = CategoriaInventario.query.count()
            productos_count = Producto.query.count()
            movimientos_count = MovimientoInventario.query.count()
            
            print(f"👤 Usuarios: {usuarios_count}")
            print(f"👥 Empleados: {empleados_count}")
            print(f"📅 Asistencias: {asistencias_count}")
            print(f"🚪 Visitantes: {visitantes_count}")
            print(f"📄 Contratos: {contratos_count}")
            print(f"📄 Contratos generados: {contratos_generados_count}")
            print(f"🏷️  Categorías: {categorias_count}")
            print(f"📦 Productos: {productos_count}")
            print(f"🔄 Movimientos: {movimientos_count}")
            
            # Verificar administrador
            admin_user = User.query.filter_by(is_admin=True).first()
            if admin_user:
                print(f"\n✅ Usuario administrador: {admin_user.email}")
            else:
                print("\n❌ No se encontró usuario administrador")
            
            total_registros = (usuarios_count + empleados_count + asistencias_count + 
                             visitantes_count + contratos_count + contratos_generados_count + 
                             categorias_count + productos_count + movimientos_count)
            
            print(f"\n📊 Total de registros: {total_registros}")
            
            if total_registros <= 1:  # Solo el administrador
                print("🎯 Base de datos limpia - lista para datos reales")
            else:
                print("⚠️  Base de datos contiene datos - considera limpiar")
            
    except Exception as e:
        print(f"❌ Error al verificar estado: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🛠️  HERRAMIENTA DE LIMPIEZA DE DATOS")
    print("=" * 60)
    print("1. Verificar estado actual")
    print("2. Limpiar todos los datos")
    print("3. Salir")
    
    while True:
        try:
            opcion = input("\nSelecciona una opción (1-3): ").strip()
            
            if opcion == "1":
                verificar_estado()
            elif opcion == "2":
                if limpiar_datos():
                    print("\n🎉 ¡Limpieza completada exitosamente!")
                else:
                    print("\n❌ Error durante la limpieza")
            elif opcion == "3":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida. Selecciona 1, 2 o 3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Operación cancelada por el usuario")
            break
        except Exception as e:
            print(f"\n❌ Error inesperado: {str(e)}")
            break
