"""
Script simple para probar las notificaciones
"""

import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def probar_notificaciones():
    print("🧪 PROBANDO SISTEMA DE NOTIFICACIONES")
    print("=" * 50)
    
    try:
        # Intentar importar las funciones de notificación
        from notificaciones import (
            notificar_asistencia_entrada,
            notificar_asistencia_salida,
            notificar_visitante_nuevo,
            notificacion_manager
        )
        print("✅ Funciones de notificación importadas correctamente")
        
        # Probar crear una notificación
        print("\n🔔 Probando notificación de entrada...")
        notif_id = notificar_asistencia_entrada("Juan Pérez", "08:30")
        print(f"✅ Notificación creada con ID: {notif_id}")
        
        # Esperar un poco para que se procese
        import time
        time.sleep(2)
        
        # Verificar que se guardó en la base de datos
        print("\n📋 Verificando notificaciones en BD...")
        notificaciones = notificacion_manager.obtener_notificaciones()
        print(f"📊 Total de notificaciones: {len(notificaciones)}")
        
        if notificaciones:
            for notif in notificaciones:
                print(f"   - {notif['titulo']}: {notif['mensaje']} (ID: {notif['id']})")
        else:
            print("❌ No se encontraron notificaciones en la BD")
        
        # Verificar DB_AVAILABLE
        from notificaciones import DB_AVAILABLE
        print(f"\n💾 DB_AVAILABLE: {DB_AVAILABLE}")
        
    except ImportError as e:
        print(f"❌ Error al importar: {e}")
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    probar_notificaciones()
