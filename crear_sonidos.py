"""
Script para crear sonidos básicos para las notificaciones
"""

import numpy as np
import os

def crear_sonidos():
    """Crea archivos de sonido básicos para las notificaciones"""
    
    # Crear directorio si no existe
    directorio = 'sounds'
    if not os.path.exists(directorio):
        os.makedirs(directorio)
    
    # Configuración de audio
    sample_rate = 44100
    duracion = 0.5
    
    try:
        # Sonido de entrada (tono ascendente)
        print("🎵 Creando sonido de entrada...")
        t = np.linspace(0, duracion, int(sample_rate * duracion))
        frecuencia_inicial = 400
        frecuencia_final = 800
        
        # Crear tono ascendente
        frecuencias = np.linspace(frecuencia_inicial, frecuencia_final, len(t))
        sonido_entrada = np.sin(2 * np.pi * frecuencias * t) * 0.3
        
        # Aplicar envelope (fade in/out)
        envelope = np.exp(-t * 2) * (1 - np.exp(-t * 10))
        sonido_entrada *= envelope
        
        # Guardar como WAV
        with open(os.path.join(directorio, 'entrada.wav'), 'wb') as f:
            # Header WAV básico
            f.write(b'RIFF')
            f.write((len(sonido_entrada) * 2 + 36).to_bytes(4, 'little'))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))  # Tamaño del header
            f.write((1).to_bytes(2, 'little'))   # PCM
            f.write((1).to_bytes(2, 'little'))   # Mono
            f.write(sample_rate.to_bytes(4, 'little'))
            f.write((sample_rate * 2).to_bytes(4, 'little'))  # Byte rate
            f.write((2).to_bytes(2, 'little'))   # Block align
            f.write((16).to_bytes(2, 'little'))  # Bits per sample
            f.write(b'data')
            f.write((len(sonido_entrada) * 2).to_bytes(4, 'little'))
            
            # Datos de audio (16-bit PCM)
            for sample in sonido_entrada:
                f.write(int(sample * 32767).to_bytes(2, 'little', signed=True))
        
        # Sonido de salida (tono descendente)
        print("🎵 Creando sonido de salida...")
        frecuencias = np.linspace(frecuencia_final, frecuencia_inicial, len(t))
        sonido_salida = np.sin(2 * np.pi * frecuencias * t) * 0.3
        sonido_salida *= envelope
        
        with open(os.path.join(directorio, 'salida.wav'), 'wb') as f:
            f.write(b'RIFF')
            f.write((len(sonido_salida) * 2 + 36).to_bytes(4, 'little'))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))
            f.write((1).to_bytes(2, 'little'))
            f.write((1).to_bytes(2, 'little'))
            f.write(sample_rate.to_bytes(4, 'little'))
            f.write((sample_rate * 2).to_bytes(4, 'little'))
            f.write((2).to_bytes(2, 'little'))
            f.write((16).to_bytes(2, 'little'))
            f.write(b'data')
            f.write((len(sonido_salida) * 2).to_bytes(4, 'little'))
            
            for sample in sonido_salida:
                f.write(int(sample * 32767).to_bytes(2, 'little', signed=True))
        
        # Sonido de visitante (dos tonos)
        print("🎵 Creando sonido de visitante...")
        t_corto = np.linspace(0, duracion/2, int(sample_rate * duracion/2))
        sonido_visitante = np.concatenate([
            np.sin(2 * np.pi * 600 * t_corto) * 0.3,
            np.sin(2 * np.pi * 900 * t_corto) * 0.3
        ])
        
        # Envelope para el sonido completo
        t_completo = np.linspace(0, duracion, len(sonido_visitante))
        envelope_visitante = np.exp(-t_completo * 3) * (1 - np.exp(-t_completo * 15))
        sonido_visitante *= envelope_visitante
        
        with open(os.path.join(directorio, 'visitante.wav'), 'wb') as f:
            f.write(b'RIFF')
            f.write((len(sonido_visitante) * 2 + 36).to_bytes(4, 'little'))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))
            f.write((1).to_bytes(2, 'little'))
            f.write((1).to_bytes(2, 'little'))
            f.write(sample_rate.to_bytes(4, 'little'))
            f.write((sample_rate * 2).to_bytes(4, 'little'))
            f.write((2).to_bytes(2, 'little'))
            f.write((16).to_bytes(2, 'little'))
            f.write(b'data')
            f.write((len(sonido_visitante) * 2).to_bytes(4, 'little'))
            
            for sample in sonido_visitante:
                f.write(int(sample * 32767).to_bytes(2, 'little', signed=True))
        
        # Sonido de alerta (tres tonos rápidos)
        print("🎵 Creando sonido de alerta...")
        duracion_tono = 0.15
        silencio = 0.05
        t_tono = np.linspace(0, duracion_tono, int(sample_rate * duracion_tono))
        t_silencio = np.linspace(0, silencio, int(sample_rate * silencio))
        
        tono = np.sin(2 * np.pi * 1000 * t_tono) * 0.4
        silencio_audio = np.zeros_like(t_silencio)
        
        sonido_alerta = np.concatenate([
            tono, silencio_audio, tono, silencio_audio, tono
        ])
        
        # Envelope suave
        t_alerta = np.linspace(0, len(sonido_alerta)/sample_rate, len(sonido_alerta))
        envelope_alerta = np.exp(-t_alerta * 4)
        sonido_alerta *= envelope_alerta
        
        with open(os.path.join(directorio, 'alerta.wav'), 'wb') as f:
            f.write(b'RIFF')
            f.write((len(sonido_alerta) * 2 + 36).to_bytes(4, 'little'))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))
            f.write((1).to_bytes(2, 'little'))
            f.write((1).to_bytes(2, 'little'))
            f.write(sample_rate.to_bytes(4, 'little'))
            f.write((sample_rate * 2).to_bytes(4, 'little'))
            f.write((2).to_bytes(2, 'little'))
            f.write((16).to_bytes(2, 'little'))
            f.write(b'data')
            f.write((len(sonido_alerta) * 2).to_bytes(4, 'little'))
            
            for sample in sonido_alerta:
                f.write(int(sample * 32767).to_bytes(2, 'little', signed=True))
        
        print("✅ Todos los sonidos creados exitosamente!")
        print(f"📁 Sonidos guardados en: {os.path.abspath(directorio)}")
        
    except Exception as e:
        print(f"❌ Error creando sonidos: {e}")
        print("💡 Asegúrate de tener numpy instalado: pip install numpy")

if __name__ == "__main__":
    crear_sonidos()
