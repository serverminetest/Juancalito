"""
Sistema de Notificaciones con Sonido
Maneja notificaciones en tiempo real y sonidos para la aplicación
"""

import json
import time
from datetime import datetime
from flask import jsonify
import threading
import queue
import os

# Intentar importar playsound, si no está disponible usar un fallback
try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False
    print("⚠️ playsound no está disponible. Las notificaciones de sonido estarán deshabilitadas.")

class NotificacionManager:
    def __init__(self):
        self.notificaciones = []
        self.sonidos_disponibles = {
            'entrada': 'sounds/entrada.mp3',
            'salida': 'sounds/salida.mp3', 
            'visitante': 'sounds/visitante.mp3',
            'alerta': 'sounds/alerta.mp3'
        }
        self.queue_notificaciones = queue.Queue()
        self.thread_procesador = None
        self.iniciar_procesador()
    
    def iniciar_procesador(self):
        """Inicia el hilo que procesa las notificaciones"""
        if self.thread_procesador is None or not self.thread_procesador.is_alive():
            self.thread_procesador = threading.Thread(target=self._procesar_notificaciones, daemon=True)
            self.thread_procesador.start()
    
    def _procesar_notificaciones(self):
        """Procesa las notificaciones en cola"""
        while True:
            try:
                notificacion = self.queue_notificaciones.get(timeout=1)
                if notificacion is None:
                    break
                
                # Agregar a la lista de notificaciones
                self.notificaciones.append(notificacion)
                
                # Reproducir sonido si está disponible
                self._reproducir_sonido(notificacion.get('tipo_sonido', 'alerta'))
                
                # Limpiar notificaciones antiguas (mantener solo las últimas 50)
                if len(self.notificaciones) > 50:
                    self.notificaciones = self.notificaciones[-50:]
                
                self.queue_notificaciones.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error procesando notificación: {e}")
    
    def _reproducir_sonido(self, tipo_sonido):
        """Reproduce un sonido según el tipo"""
        if not PLAYSOUND_AVAILABLE:
            return
        
        archivo_sonido = self.sonidos_disponibles.get(tipo_sonido)
        if not archivo_sonido or not os.path.exists(archivo_sonido):
            # Usar sonido por defecto si no existe el específico
            archivo_sonido = self.sonidos_disponibles.get('alerta')
        
        if archivo_sonido and os.path.exists(archivo_sonido):
            try:
                # Reproducir en un hilo separado para no bloquear
                threading.Thread(
                    target=lambda: playsound(archivo_sonido, block=False),
                    daemon=True
                ).start()
            except Exception as e:
                print(f"Error reproduciendo sonido: {e}")
    
    def agregar_notificacion(self, titulo, mensaje, tipo='info', tipo_sonido='alerta', icono='fas fa-bell'):
        """Agrega una nueva notificación"""
        notificacion = {
            'id': int(time.time() * 1000),  # ID único basado en timestamp
            'titulo': titulo,
            'mensaje': mensaje,
            'tipo': tipo,  # success, info, warning, error
            'tipo_sonido': tipo_sonido,
            'icono': icono,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'leida': False
        }
        
        self.queue_notificaciones.put(notificacion)
        return notificacion['id']
    
    def obtener_notificaciones(self, no_leidas=False):
        """Obtiene las notificaciones"""
        if no_leidas:
            return [n for n in self.notificaciones if not n['leida']]
        return self.notificaciones
    
    def marcar_como_leida(self, notificacion_id):
        """Marca una notificación como leída"""
        for notificacion in self.notificaciones:
            if notificacion['id'] == notificacion_id:
                notificacion['leida'] = True
                break
    
    def limpiar_notificaciones(self):
        """Limpia todas las notificaciones"""
        self.notificaciones.clear()
    
    def crear_sonidos_por_defecto(self):
        """Crea archivos de sonido por defecto si no existen"""
        directorio_sonidos = 'sounds'
        if not os.path.exists(directorio_sonidos):
            os.makedirs(directorio_sonidos)
        
        # Crear archivos de sonido básicos usando frecuencias
        try:
            import numpy as np
            import soundfile as sf
            
            # Sonido de entrada (tono ascendente)
            frecuencia = 800
            duracion = 0.5
            muestras = int(44100 * duracion)
            t = np.linspace(0, duracion, muestras)
            sonido_entrada = np.sin(2 * np.pi * frecuencia * t) * 0.3
            
            # Sonido de salida (tono descendente)
            frecuencia_inicial = 600
            frecuencia_final = 300
            sonido_salida = np.sin(2 * np.pi * np.linspace(frecuencia_inicial, frecuencia_final, muestras) * t) * 0.3
            
            # Sonido de visitante (dos tonos)
            sonido_visitante = np.concatenate([
                np.sin(2 * np.pi * 500 * t[:muestras//2]) * 0.3,
                np.sin(2 * np.pi * 700 * t[muestras//2:]) * 0.3
            ])
            
            # Sonido de alerta (tres tonos rápidos)
            tono_corto = int(44100 * 0.2)
            sonido_alerta = np.concatenate([
                np.sin(2 * np.pi * 1000 * t[:tono_corto]) * 0.3,
                np.zeros(tono_corto//2),
                np.sin(2 * np.pi * 1000 * t[:tono_corto]) * 0.3,
                np.zeros(tono_corto//2),
                np.sin(2 * np.pi * 1000 * t[:tono_corto]) * 0.3
            ])
            
            # Guardar archivos
            sf.write(os.path.join(directorio_sonidos, 'entrada.wav'), sonido_entrada, 44100)
            sf.write(os.path.join(directorio_sonidos, 'salida.wav'), sonido_salida, 44100)
            sf.write(os.path.join(directorio_sonidos, 'visitante.wav'), sonido_visitante, 44100)
            sf.write(os.path.join(directorio_sonidos, 'alerta.wav'), sonido_alerta, 44100)
            
            print("✅ Sonidos por defecto creados exitosamente")
            
        except ImportError:
            print("⚠️ numpy y soundfile no están disponibles. No se pueden crear sonidos por defecto.")
        except Exception as e:
            print(f"⚠️ Error creando sonidos por defecto: {e}")

# Instancia global del manager de notificaciones
notificacion_manager = NotificacionManager()

def notificar_asistencia_entrada(empleado_nombre, hora):
    """Notifica cuando un empleado registra entrada"""
    titulo = "Entrada Registrada"
    mensaje = f"{empleado_nombre} registró entrada a las {hora}"
    return notificacion_manager.agregar_notificacion(
        titulo=titulo,
        mensaje=mensaje,
        tipo='success',
        tipo_sonido='entrada',
        icono='fas fa-sign-in-alt'
    )

def notificar_asistencia_salida(empleado_nombre, hora):
    """Notifica cuando un empleado registra salida"""
    titulo = "Salida Registrada"
    mensaje = f"{empleado_nombre} registró salida a las {hora}"
    return notificacion_manager.agregar_notificacion(
        titulo=titulo,
        mensaje=mensaje,
        tipo='info',
        tipo_sonido='salida',
        icono='fas fa-sign-out-alt'
    )

def notificar_visitante_nuevo(visitante_nombre, empresa):
    """Notifica cuando llega un nuevo visitante"""
    titulo = "Nuevo Visitante"
    mensaje = f"{visitante_nombre} ({empresa}) ha llegado"
    return notificacion_manager.agregar_notificacion(
        titulo=titulo,
        mensaje=mensaje,
        tipo='warning',
        tipo_sonido='visitante',
        icono='fas fa-user-friends'
    )

def notificar_visitante_salida(visitante_nombre):
    """Notifica cuando un visitante se va"""
    titulo = "Visitante Se Fue"
    mensaje = f"{visitante_nombre} ha salido de las instalaciones"
    return notificacion_manager.agregar_notificacion(
        titulo=titulo,
        mensaje=mensaje,
        tipo='info',
        tipo_sonido='salida',
        icono='fas fa-user-times'
    )

def notificar_error(titulo, mensaje):
    """Notifica un error"""
    return notificacion_manager.agregar_notificacion(
        titulo=titulo,
        mensaje=mensaje,
        tipo='error',
        tipo_sonido='alerta',
        icono='fas fa-exclamation-triangle'
    )

def notificar_exito(titulo, mensaje):
    """Notifica un éxito"""
    return notificacion_manager.agregar_notificacion(
        titulo=titulo,
        mensaje=mensaje,
        tipo='success',
        tipo_sonido='alerta',
        icono='fas fa-check-circle'
    )

# Funciones para la API
def obtener_notificaciones_api(no_leidas=False):
    """API para obtener notificaciones"""
    notificaciones = notificacion_manager.obtener_notificaciones(no_leidas)
    return jsonify({
        'success': True,
        'notificaciones': notificaciones,
        'total': len(notificaciones),
        'no_leidas': len([n for n in notificaciones if not n['leida']])
    })

def marcar_notificacion_leida_api(notificacion_id):
    """API para marcar notificación como leída"""
    try:
        notificacion_manager.marcar_como_leida(notificacion_id)
        return jsonify({'success': True, 'message': 'Notificación marcada como leída'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def limpiar_notificaciones_api():
    """API para limpiar todas las notificaciones"""
    try:
        notificacion_manager.limpiar_notificaciones()
        return jsonify({'success': True, 'message': 'Notificaciones limpiadas'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
