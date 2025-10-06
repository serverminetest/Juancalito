#!/usr/bin/env python3
"""
Script para limpiar todos los datos en Railway (producción)
Mantiene solo el usuario administrador
"""

import os
import sys
from datetime import datetime

# Configurar variables de entorno para Railway
if 'DATABASE_PUBLIC_URL' in os.environ:
    os.environ['DATABASE_URL'] = os.environ['DATABASE_PUBLIC_URL']

def limpiar_datos_railway():
    """Limpiar todos los datos en Railway"""
    
    print("🧹 LIMPIANDO DATOS EN RAILWAY")
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
            print("📊 Conectando a la base de datos de Railway...")
            
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
            
            if (empleados_count + asistencias_count + visitantes_count + 
                contratos_count + contratos_generados_count + 
                categorias_count + productos_count + movimientos_count) == 0:
                print("\n✅ La base de datos ya está limpia!")
                return True
            
            print("\n🗑️  Iniciando limpieza de datos...")
            
            # Eliminar datos en orden correcto (respetando foreign keys)
            
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
            
    except Exception as e:
        print(f"\n❌ Error durante la limpieza: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🛠️  LIMPIEZA DE DATOS EN RAILWAY")
    print("=" * 60)
    print("⚠️  Este script eliminará TODOS los datos excepto el usuario administrador")
    print("📋 Datos que se eliminarán:")
    print("   • Empleados, Asistencias, Visitantes")
    print("   • Contratos y contratos generados")
    print("   • Categorías, Productos y Movimientos de inventario")
    print("\n✅ Datos que se mantendrán:")
    print("   • Usuario administrador")
    
    respuesta = input("\n¿Continuar con la limpieza? (escribe 'SI' para confirmar): ")
    
    if respuesta == 'SI':
        if limpiar_datos_railway():
            print("\n🎉 ¡Limpieza completada exitosamente!")
        else:
            print("\n❌ Error durante la limpieza")
    else:
        print("❌ Operación cancelada")
