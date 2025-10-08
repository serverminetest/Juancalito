"""
Script para probar el sistema de notificaciones
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from notificaciones import (
    notificar_asistencia_entrada,
    notificar_asistencia_salida,
    notificar_visitante_nuevo,
    notificar_visitante_salida,
    notificacion_manager
)

def probar_notificaciones():
    print("🧪 Probando sistema de notificaciones...")
    
    # Probar notificación de entrada
    print("\n1. Probando notificación de entrada...")
    notificar_asistencia_entrada("Juan Pérez", "08:30")
    
    # Esperar un poco
    import time
    time.sleep(1)
    
    # Probar notificación de salida
    print("\n2. Probando notificación de salida...")
    notificar_asistencia_salida("Juan Pérez", "17:30")
    
    time.sleep(1)
    
    # Probar notificación de visitante
    print("\n3. Probando notificación de visitante...")
    notificar_visitante_nuevo("María García", "Empresa ABC")
    
    time.sleep(1)
    
    # Probar notificación de salida de visitante
    print("\n4. Probando notificación de salida de visitante...")
    notificar_visitante_salida("María García")
    
    time.sleep(2)
    
    # Verificar notificaciones
    print("\n📋 Notificaciones creadas:")
    notificaciones = notificacion_manager.obtener_notificaciones()
    for i, notif in enumerate(notificaciones, 1):
        print(f"{i}. {notif['titulo']}: {notif['mensaje']} ({notif['timestamp']})")
    
    print(f"\n✅ Total de notificaciones: {len(notificaciones)}")
    print("🎯 Prueba completada!")

if __name__ == "__main__":
    probar_notificaciones()
