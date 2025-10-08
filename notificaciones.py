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

# Intentar importar db y Notificacion desde app.py
# Usar import lazy para evitar import circular
DB_AVAILABLE = False
db = None
Notificacion = None

def _import_db_models():
    global DB_AVAILABLE, db, Notificacion
    if not DB_AVAILABLE:
        try:
            from app import db as _db, Notificacion as _Notificacion
            db = _db
            Notificacion = _Notificacion
            DB_AVAILABLE = True
            print("✅ DB y Notificacion importados correctamente")
        except ImportError as e:
            print(f"⚠️ No se pudo importar db y Notificacion de app.py: {e}")
            DB_AVAILABLE = False
        except Exception as e:
            print(f"⚠️ Error al importar db y Notificacion: {e}")
            DB_AVAILABLE = False
    return DB_AVAILABLE

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
            'entrada': 'sounds/entrada.wav',
            'salida': 'sounds/salida.wav', 
            'visitante': 'sounds/visitante.wav',
            'alerta': 'sounds/alerta.wav'
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
                notificacion_data = self.queue_notificaciones.get(timeout=1)
                if notificacion_data is None:
                    break
                
                print(f"⚙️ Procesando notificación: {notificacion_data['titulo']}")

                # Guardar en la base de datos si está disponible
                if _import_db_models():
                    try:
                        # Usar el contexto de aplicación actual
                        from flask import current_app
                        app = current_app._get_current_object() if hasattr(current_app, '_get_current_object') else current_app
                        
                        with app.app_context():
                            nueva_notificacion_db = Notificacion(
                                titulo=notificacion_data['titulo'],
                                mensaje=notificacion_data['mensaje'],
                                tipo=notificacion_data['tipo'],
                                tipo_sonido=notificacion_data['tipo_sonido'],
                                icono=notificacion_data['icono'],
                                fecha_creacion=datetime.fromisoformat(notificacion_data['fecha_creacion']),
                                leida=False,
                                usuario_id=notificacion_data.get('usuario_id')
                            )
                            db.session.add(nueva_notificacion_db)
                            db.session.commit()
                            notificacion_data['id'] = nueva_notificacion_db.id
                            print(f"✅ Notificación guardada en BD con ID: {nueva_notificacion_db.id}")
                    except Exception as e:
                        try:
                            db.session.rollback()
                        except:
                            pass
                        print(f"❌ Error al guardar notificación en BD: {e}")

                # Agregar a la lista de notificaciones (para compatibilidad)
                self.notificaciones.append(notificacion_data)
                
                # Reproducir sonido si está disponible
                self._reproducir_sonido(notificacion_data.get('tipo_sonido', 'alerta'))
                
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
        try:
            archivo_sonido = self.sonidos_disponibles.get(tipo_sonido)
            if not archivo_sonido or not os.path.exists(archivo_sonido):
                # Usar sonido por defecto si no existe el específico
                archivo_sonido = self.sonidos_disponibles.get('alerta')
            
            if archivo_sonido and os.path.exists(archivo_sonido):
                print(f"🔊 Reproduciendo sonido: {archivo_sonido}")
                
                if PLAYSOUND_AVAILABLE:
                    # Reproducir en un hilo separado para no bloquear
                    threading.Thread(
                        target=lambda: playsound(archivo_sonido, block=False),
                        daemon=True
                    ).start()
                else:
                    print("⚠️ playsound no disponible, usando sonido del navegador")
        except Exception as e:
            print(f"Error reproduciendo sonido: {e}")
    
    def agregar_notificacion(self, titulo, mensaje, tipo='info', tipo_sonido='alerta', icono='fas fa-bell', usuario_id=None):
        """Agrega una nueva notificación"""
        ahora = datetime.now()
        temp_id = int(time.time() * 1000)
        
        notificacion_data = {
            'id': temp_id,
            'titulo': titulo,
            'mensaje': mensaje,
            'tipo': tipo,
            'tipo_sonido': tipo_sonido,
            'icono': icono,
            'fecha_creacion': ahora.isoformat(),
            'leida': False,
            'usuario_id': usuario_id
        }
        
        print(f"🔔 Agregando notificación: {titulo} - {mensaje}")
        
        # Guardar directamente en la BD si estamos en contexto de Flask
        if _import_db_models():
            try:
                from flask import current_app
                with current_app.app_context():
                    nueva_notificacion_db = Notificacion(
                        titulo=notificacion_data['titulo'],
                        mensaje=notificacion_data['mensaje'],
                        tipo=notificacion_data['tipo'],
                        tipo_sonido=notificacion_data['tipo_sonido'],
                        icono=notificacion_data['icono'],
                        fecha_creacion=datetime.fromisoformat(notificacion_data['fecha_creacion']),
                        leida=False,
                        usuario_id=notificacion_data.get('usuario_id')
                    )
                    db.session.add(nueva_notificacion_db)
                    db.session.commit()
                    notificacion_data['id'] = nueva_notificacion_db.id
                    print(f"✅ Notificación guardada directamente en BD con ID: {nueva_notificacion_db.id}")
            except Exception as e:
                print(f"❌ Error al guardar notificación directamente en BD: {e}")
                # Si falla, agregar a la cola como fallback
                self.queue_notificaciones.put(notificacion_data)
        else:
            # Si no hay BD, agregar a la cola
            self.queue_notificaciones.put(notificacion_data)
        
        return notificacion_data['id']
    
    def obtener_notificaciones(self, no_leidas=False):
        """Obtiene las notificaciones de la base de datos"""
        if _import_db_models():
            try:
                from flask import current_app
                with current_app.app_context():
                    query = Notificacion.query
                    if no_leidas:
                        query = query.filter_by(leida=False)
                    # Ordenar por fecha_creacion descendente
                    notificaciones_db = query.order_by(Notificacion.fecha_creacion.desc()).all()
                    
                    # Convertir objetos del modelo a diccionarios para jsonify
                    result = []
                    for n in notificaciones_db:
                        result.append({
                            'id': n.id,
                            'titulo': n.titulo,
                            'mensaje': n.mensaje,
                            'tipo': n.tipo,
                            'tipo_sonido': n.tipo_sonido,
                            'icono': n.icono,
                            'fecha_creacion': n.fecha_creacion.isoformat(),
                            'leida': n.leida,
                            'usuario_id': n.usuario_id
                        })
                    return result
            except Exception as e:
                print(f"❌ Error al obtener notificaciones de la BD: {e}")
                return []
        else:
            # Fallback a la lista en memoria
            if no_leidas:
                return [n for n in self.notificaciones if not n['leida']]
            return self.notificaciones
    
    def marcar_como_leida(self, notificacion_id):
        """Marca una notificación como leída"""
        if _import_db_models():
            try:
                from flask import current_app
                with current_app.app_context():
                    notificacion = Notificacion.query.get(notificacion_id)
                    if notificacion:
                        notificacion.leida = True
                        db.session.commit()
                        print(f"✅ Notificación {notificacion_id} marcada como leída en BD")
                        return True
                    else:
                        print(f"⚠️ Notificación {notificacion_id} no encontrada")
                        return False
            except Exception as e:
                print(f"❌ Error marcando notificación como leída: {e}")
                return False
        
        # Fallback a la lista en memoria
        for notificacion in self.notificaciones:
            if notificacion['id'] == notificacion_id:
                notificacion['leida'] = True
                break
        return True
    
    def limpiar_notificaciones(self):
        """Limpia todas las notificaciones"""
        if _import_db_models():
            try:
                from flask import current_app
                with current_app.app_context():
                    Notificacion.query.delete()
                    db.session.commit()
                    print("🗑️ Todas las notificaciones eliminadas de la BD")
                    return True
            except Exception as e:
                print(f"❌ Error limpiando notificaciones: {e}")
                return False
        
        # Fallback a la lista en memoria
        self.notificaciones.clear()
        return True
    
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
    print(f"🚪 FUNCIÓN LLAMADA: notificar_asistencia_entrada({empleado_nombre}, {hora})")
    titulo = "Entrada Registrada"
    mensaje = f"{empleado_nombre} registró entrada a las {hora}"
    print(f"🔔 Creando notificación: {titulo} - {mensaje}")
    try:
        notif_id = notificacion_manager.agregar_notificacion(
            titulo=titulo,
            mensaje=mensaje,
            tipo='success',
            tipo_sonido='entrada',
            icono='fas fa-sign-in-alt'
        )
        print(f"✅ Notificación creada con ID: {notif_id}")
        return notif_id
    except Exception as e:
        print(f"❌ Error creando notificación: {e}")
        import traceback
        traceback.print_exc()
        return None

def notificar_asistencia_salida(empleado_nombre, hora):
    """Notifica cuando un empleado registra salida"""
    print(f"🚪 Notificando salida de {empleado_nombre} a las {hora}")
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
    print(f"👥 Notificando llegada de visitante: {visitante_nombre} ({empresa})")
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
    try:
        notificaciones = notificacion_manager.obtener_notificaciones(no_leidas)
        total_notificaciones = len(notificaciones)
        no_leidas_count = len([n for n in notificaciones if not n['leida']])
        print(f"📋 API: Obteniendo notificaciones - Total: {total_notificaciones}, No leídas: {no_leidas_count}")
        return jsonify({
            'success': True,
            'notificaciones': notificaciones,
            'total': total_notificaciones,
            'no_leidas': no_leidas_count
        })
    except Exception as e:
        print(f"❌ API Error al obtener notificaciones: {e}")
        return jsonify({'success': False, 'message': str(e), 'notificaciones': [], 'total': 0, 'no_leidas': 0}), 500

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
