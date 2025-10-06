#!/usr/bin/env python3
"""
Script para verificar el estado de los datos en la aplicación
"""

import os
import sys

# Agregar el directorio actual al path para importar app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verificar_datos():
    """Verificar el estado actual de todos los datos"""
    
    print("📊 VERIFICACIÓN DE DATOS DE LA APLICACIÓN")
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
            
            print(f"\n📋 RESUMEN DE DATOS:")
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
            
            # Verificar empleados activos
            empleados_activos = Empleado.query.filter_by(activo=True).count()
            print(f"👥 Empleados activos: {empleados_activos}")
            
            # Verificar productos con stock bajo
            productos_bajo_stock = Producto.query.filter(
                Producto.stock_actual <= Producto.stock_minimo
            ).count()
            print(f"⚠️  Productos con stock bajo: {productos_bajo_stock}")
            
            # Verificar categorías activas
            categorias_activas = CategoriaInventario.query.filter_by(activa=True).count()
            print(f"🏷️  Categorías activas: {categorias_activas}")
            
            total_registros = (usuarios_count + empleados_count + asistencias_count + 
                             visitantes_count + contratos_count + contratos_generados_count + 
                             categorias_count + productos_count + movimientos_count)
            
            print(f"\n📊 Total de registros: {total_registros}")
            
            # Estado de la base de datos
            if total_registros <= 1:  # Solo el administrador
                print("\n🎯 Estado: Base de datos limpia - lista para datos reales")
                print("💡 Recomendación: Comenzar a agregar datos reales")
            elif total_registros < 10:
                print("\n🔄 Estado: Base de datos con pocos datos")
                print("💡 Recomendación: Continuar agregando datos")
            else:
                print("\n📈 Estado: Base de datos con datos significativos")
                print("💡 Recomendación: Sistema en uso normal")
            
            # Mostrar algunos ejemplos
            if empleados_count > 0:
                print(f"\n👥 Primeros empleados:")
                empleados = Empleado.query.limit(3).all()
                for emp in empleados:
                    print(f"   • {emp.nombre_completo} ({emp.cargo})")
            
            if productos_count > 0:
                print(f"\n📦 Primeros productos:")
                productos = Producto.query.limit(3).all()
                for prod in productos:
                    print(f"   • {prod.nombre} - Stock: {prod.stock_actual}")
            
            if categorias_count > 0:
                print(f"\n🏷️  Categorías disponibles:")
                categorias = CategoriaInventario.query.all()
                for cat in categorias:
                    print(f"   • {cat.nombre} ({'Activa' if cat.activa else 'Inactiva'})")
            
    except Exception as e:
        print(f"❌ Error al verificar datos: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    verificar_datos()
