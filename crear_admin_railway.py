#!/usr/bin/env python3
"""
Script para crear usuario admin directamente en Railway
Ejecutar desde Railway: python crear_admin_railway.py
"""

import os
from app import app, db, User
from werkzeug.security import generate_password_hash

def crear_usuario_admin():
    """Crear usuario admin para la jefa"""
    
    with app.app_context():
        print("=" * 60)
        print("CREANDO USUARIO ADMIN PARA LA JEFA")
        print("=" * 60)
        
        # Datos del usuario
        email = "floresjuncalito@gmail.com"
        username = "admin_jefa"
        password = "123456789"
        
        print(f"Email: {email}")
        print(f"Username: {username}")
        print(f"Contraseña: {password}")
        print("=" * 60)
        
        # Verificar si ya existe
        usuario_existente = User.query.filter_by(email=email).first()
        
        if usuario_existente:
            print(f"⚠️ Usuario ya existe con ID: {usuario_existente.id}")
            print("🔄 Actualizando contraseña...")
            
            # Generar nuevo hash
            nuevo_hash = generate_password_hash(password)
            usuario_existente.password_hash = nuevo_hash
            usuario_existente.username = username
            usuario_existente.is_admin = True
            
            try:
                db.session.commit()
                print("✅ Usuario actualizado exitosamente")
                print(f"   Nuevo hash: {nuevo_hash[:50]}...")
            except Exception as e:
                print(f"❌ Error al actualizar: {e}")
                db.session.rollback()
                return False
        else:
            print("➕ Creando nuevo usuario...")
            
            # Generar hash de contraseña
            password_hash = generate_password_hash(password)
            
            # Crear usuario
            nuevo_usuario = User(
                email=email,
                username=username,
                password_hash=password_hash,
                is_admin=True
            )
            
            try:
                db.session.add(nuevo_usuario)
                db.session.commit()
                print("✅ Usuario creado exitosamente")
                print(f"   ID: {nuevo_usuario.id}")
                print(f"   Hash: {password_hash[:50]}...")
            except Exception as e:
                print(f"❌ Error al crear usuario: {e}")
                db.session.rollback()
                return False
        
        # Verificar creación
        print("\n🔍 Verificando usuario...")
        usuario_verificado = User.query.filter_by(email=email).first()
        
        if usuario_verificado:
            print("✅ Usuario verificado:")
            print(f"   ID: {usuario_verificado.id}")
            print(f"   Email: {usuario_verificado.email}")
            print(f"   Username: {usuario_verificado.username}")
            print(f"   Is Admin: {usuario_verificado.is_admin}")
            
            # Probar contraseña
            from werkzeug.security import check_password_hash
            if check_password_hash(usuario_verificado.password_hash, password):
                print("✅ Contraseña verificada correctamente")
            else:
                print("❌ Error en verificación de contraseña")
                
        print("=" * 60)
        print("🎉 PROCESO COMPLETADO")
        print("=" * 60)
        print("DATOS DE ACCESO:")
        print(f"Email: {email}")
        print(f"Contraseña: {password}")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    crear_usuario_admin()
