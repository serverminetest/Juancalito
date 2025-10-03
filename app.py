from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import text
import os
import qrcode
import io
import hashlib
import secrets
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
import shutil

# Configurar zona horaria de Colombia (UTC-5)
COLOMBIA_TZ = timezone(timedelta(hours=-5))

def colombia_now():
    """Devuelve la fecha y hora actual en zona horaria de Colombia"""
    return datetime.now(COLOMBIA_TZ)

def to_colombia_time(dt):
    """Convierte una fecha/hora a zona horaria de Colombia"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Si no tiene zona horaria, asumir que es UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(COLOMBIA_TZ)

def generar_contrato_excel(contrato_id):
    """Genera un contrato Excel basado en el template y los datos del empleado"""
    try:
        # Obtener datos del contrato y empleado
        contrato = Contrato.query.get_or_404(contrato_id)
        empleado = contrato.empleado
        
        # Cargar template Excel
        template_path = 'CONTRATO EXCEL FLORE JUNCALITO.xlsx'
        if not os.path.exists(template_path):
            raise FileNotFoundError("Template de contrato no encontrado")
        
        # Crear directorio para contratos generados
        contratos_dir = 'contratos_generados'
        if not os.path.exists(contratos_dir):
            os.makedirs(contratos_dir)
        
        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"Contrato_{empleado.nombre_completo.replace(' ', '_')}_{timestamp}.xlsx"
        ruta_archivo = os.path.join(contratos_dir, nombre_archivo)
        
        # Copiar template y cargar workbook
        shutil.copy2(template_path, ruta_archivo)
        workbook = load_workbook(ruta_archivo)
        worksheet = workbook.active
        
        # Datos del empleador (predeterminados según la imagen)
        datos_empleador = {
            'NOMBRE_EMPLEADOR': 'FLORES JUNCALITO S.A.S',
            'DIRECCION_EMPLEADOR': 'CALLE 19* C N. 88-07'
        }
        
        # Datos del empleado
        datos_empleado = {
            'NOMBRE_EMPLEADO': empleado.nombre_completo.upper(),
            'NOMBRE_TRABAJADOR': empleado.nombre_completo.upper(),
            'DIRECCION_EMPLEADO': (empleado.direccion_residencia or 'NO ESPECIFICADA').upper(),
            'DIRECCION_TRABAJADOR': (empleado.direccion_residencia or 'NO ESPECIFICADA').upper(),
            'LUGAR_NACIMIENTO': (empleado.ciudad or 'BOGOTÁ, COLOMBIA').upper(),
            'FECHA_NACIMIENTO': convertir_fecha_espanol(empleado.fecha_nacimiento),
            'CARGO_EMPLEADO': (empleado.cargo_puesto or 'NO ESPECIFICADO').upper(),
            'CARGO': (empleado.cargo_puesto or 'NO ESPECIFICADO').upper(),
            'SALARIO_NUMEROS': f"$ {contrato.salario:,.0f}",
            'SALARIO': f"$ {contrato.salario:,.0f}",
            'SALARIO_LETRAS': convertir_numero_a_letras(contrato.salario),
            'VALOR_LETRAS': convertir_numero_a_letras(contrato.salario),
            'FECHA_INICIO_LABORES': convertir_fecha_espanol(contrato.fecha_inicio),
            'FECHA_INICIO': convertir_fecha_espanol(contrato.fecha_inicio),
            'FECHA_FIN': convertir_fecha_espanol(contrato.fecha_fin) if contrato.fecha_fin else 'INDEFINIDO',
            'VENCE_EL_DIA': convertir_fecha_espanol(contrato.fecha_fin) if contrato.fecha_fin else 'INDEFINIDO',
            'LUGAR_LABORES': 'FLORES JUNCALITO S.A.S',
            'LUGAR_TRABAJO': 'FLORES JUNCALITO S.A.S',
            'CIUDAD_CONTRATACION': 'EL ROSAL CUNDINAMARCA',
            'CIUDAD_CONTRATO': 'EL ROSAL CUNDINAMARCA',
            'TIPO_SALARIO': 'ORDINARIO',
            'PERIODOS_PAGO': 'MENSUAL'
        }
        
        # Combinar todos los datos
        todos_datos = {**datos_empleador, **datos_empleado}
        
        # Reemplazar variables en el Excel
        reemplazar_variables_excel(worksheet, todos_datos)
        
        # Guardar el archivo
        workbook.save(ruta_archivo)
        
        # Leer el archivo como datos binarios
        with open(ruta_archivo, 'rb') as f:
            archivo_data = f.read()
        
        # Verificar si la tabla contrato_generado existe antes de insertar
        try:
            # Intentar crear la tabla si no existe
            try:
                with db.engine.connect() as connection:
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS contrato_generado (
                            id SERIAL PRIMARY KEY,
                            empleado_id INTEGER NOT NULL REFERENCES empleado(id),
                            contrato_id INTEGER NOT NULL REFERENCES contrato(id),
                            nombre_archivo VARCHAR(255) NOT NULL,
                            ruta_archivo VARCHAR(500) NOT NULL,
                            archivo_data BYTEA,
                            fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            activo BOOLEAN DEFAULT TRUE
                        );
                    """))
                    connection.commit()
                print("✅ Tabla contrato_generado creada/verificada en generar_contrato_excel")
            except Exception as create_error:
                print(f"⚠️ No se pudo crear la tabla en generar_contrato_excel: {create_error}")
            
            # Registrar en la base de datos con datos binarios
            contrato_generado = ContratoGenerado(
                empleado_id=empleado.id,
                contrato_id=contrato.id,
                nombre_archivo=nombre_archivo,
                ruta_archivo=ruta_archivo,
                archivo_data=archivo_data
            )
            db.session.add(contrato_generado)
            db.session.commit()
            
            # Limpiar archivo temporal (opcional, ya que tenemos los datos en BD)
            try:
                os.remove(ruta_archivo)
                print(f"✅ Archivo temporal eliminado: {ruta_archivo}")
            except:
                pass  # No es crítico si no se puede eliminar
            
            print(f"✅ Contrato generado y guardado en BD: {nombre_archivo}")
            return contrato_generado
        except Exception as db_error:
            print(f"Error al guardar en base de datos: {str(db_error)}")
            # Si hay error de BD, crear un objeto mock que simule ContratoGenerado
            class MockContratoGenerado:
                def __init__(self, nombre_archivo, ruta_archivo, empleado, contrato, archivo_data):
                    self.nombre_archivo = nombre_archivo
                    self.ruta_archivo = ruta_archivo
                    self.archivo_data = archivo_data
                    self.empleado = empleado
                    self.contrato = contrato
                    self.id = None  # No tiene ID porque no se guardó en BD
            
            return MockContratoGenerado(nombre_archivo, ruta_archivo, empleado, contrato, archivo_data)
        
    except Exception as e:
        print(f"Error al generar contrato: {str(e)}")
        raise

def reemplazar_variables_excel(worksheet, datos):
    """Reemplaza las variables {VARIABLE} en el Excel con los datos reales"""
    try:
        variables_reemplazadas = 0
        variables_no_encontradas = []
        
        # Recorrer todas las celdas del worksheet
        for row in worksheet.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    # Buscar variables en formato {VARIABLE}
                    import re
                    variables_encontradas = re.findall(r'\{([^}]+)\}', cell.value)
                    
                    if variables_encontradas:
                        valor_original = cell.value
                        valor_nuevo = valor_original
                        
                        # Reemplazar cada variable encontrada
                        for variable in variables_encontradas:
                            if variable in datos:
                                valor_nuevo = valor_nuevo.replace(f'{{{variable}}}', str(datos[variable]))
                                variables_reemplazadas += 1
                            else:
                                variables_no_encontradas.append(variable)
                                print(f"⚠️ Variable no encontrada: {variable}")
                        
                        # Actualizar el valor de la celda
                        cell.value = valor_nuevo
                        if valor_original != valor_nuevo:
                            print(f"✅ Reemplazado: {valor_original} -> {valor_nuevo}")
        
        print(f"✅ Variables reemplazadas exitosamente: {variables_reemplazadas} reemplazos")
        if variables_no_encontradas:
            print(f"⚠️ Variables no encontradas: {', '.join(set(variables_no_encontradas))}")
        
        # Mostrar todas las variables disponibles
        print(f"📋 Variables disponibles: {', '.join(datos.keys())}")
        
    except Exception as e:
        print(f"❌ Error al reemplazar variables: {str(e)}")

def convertir_numero_a_letras(numero):
    """Convierte un número a letras (mejorado para salarios)"""
    try:
        if numero == 0:
            return 'CERO PESOS'
        
        # Convertir a entero para evitar decimales
        numero = int(numero)
        
        # Nombres de números
        unidades = ['', 'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
        decenas = ['', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
        centenas = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS']
        
        # Casos especiales
        if numero == 100:
            return 'CIEN PESOS'
        if numero == 1000:
            return 'MIL PESOS'
        if numero == 1000000:
            return 'UN MILLON DE PESOS'
        
        resultado = ''
        
        # Millones
        millones = numero // 1000000
        if millones > 0:
            if millones == 1:
                resultado += 'UN MILLON '
            elif millones < 10:
                resultado += f"{unidades[millones]} MILLONES "
            else:
                # Para números mayores a 9 millones, convertir a letras
                resultado += convertir_centenas_miles(millones) + " MILLONES "
            numero = numero % 1000000
        
        # Miles
        miles = numero // 1000
        if miles > 0:
            if miles == 1:
                resultado += 'MIL '
            elif miles < 10:
                resultado += f"{unidades[miles]} MIL "
            else:
                # Para números mayores a 9 mil, convertir a letras
                resultado += convertir_centenas_miles(miles) + " MIL "
            numero = numero % 1000
        
        # Centenas, decenas y unidades restantes
        if numero > 0:
            resultado += convertir_centenas_miles(numero) + " "
        
        resultado += 'PESOS'
        return resultado.strip()
        
    except Exception as e:
        print(f"Error al convertir número a letras: {str(e)}")
        return f"{numero} PESOS"

def convertir_centenas_miles(numero):
    """Convierte números de 1 a 999 a letras"""
    if numero == 0:
        return ''
    
    unidades = ['', 'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
    decenas = ['', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
    centenas = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS']
    
    resultado = ''
    
    # Centenas
    centena = numero // 100
    if centena > 0:
        if centena == 1 and numero % 100 == 0:
            resultado += 'CIEN'
        else:
            resultado += centenas[centena]
        numero = numero % 100
    
    # Decenas y unidades
    if numero > 0:
        if numero < 10:
            resultado += unidades[numero]
        elif numero < 20:
            if numero == 10:
                resultado += 'DIEZ'
            elif numero == 11:
                resultado += 'ONCE'
            elif numero == 12:
                resultado += 'DOCE'
            elif numero == 13:
                resultado += 'TRECE'
            elif numero == 14:
                resultado += 'CATORCE'
            elif numero == 15:
                resultado += 'QUINCE'
            elif numero == 16:
                resultado += 'DIECISEIS'
            elif numero == 17:
                resultado += 'DIECISIETE'
            elif numero == 18:
                resultado += 'DIECIOCHO'
            elif numero == 19:
                resultado += 'DIECINUEVE'
        else:
            decena = numero // 10
            unidad = numero % 10
            if unidad == 0:
                resultado += decenas[decena]
            else:
                resultado += decenas[decena] + " Y " + unidades[unidad]
    
    return resultado

def convertir_fecha_espanol(fecha):
    """Convierte una fecha a formato español"""
    if fecha is None:
        return 'INDEFINIDO'
    
    # Mapeo de meses en inglés a español
    meses_espanol = {
        1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
        5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
        9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
    }
    
    try:
        dia = fecha.day
        mes = meses_espanol[fecha.month]
        año = fecha.year
        
        return f"{dia} DE {mes} DE {año}"
    except Exception as e:
        print(f"Error al convertir fecha: {str(e)}")
        return str(fecha)

def convertir_excel_a_html(worksheet, contrato_generado):
    """Convierte una hoja de Excel a HTML para vista previa"""
    try:
        html = '<div class="vista-previa-excel">'
        html += f'<div class="text-center mb-4">'
        html += f'<h4 class="text-primary"><i class="fas fa-file-excel me-2"></i>Vista Previa del Contrato</h4>'
        html += f'<p class="text-muted">Empleado: <strong>{contrato_generado.empleado.nombre_completo}</strong></p>'
        html += f'</div>'
        
        # Crear tabla HTML
        html += '<div class="table-responsive">'
        html += '<table class="table table-bordered table-sm" style="font-size: 12px;">'
        
        # Obtener dimensiones de la hoja
        max_row = worksheet.max_row
        max_col = worksheet.max_column
        
        # Procesar cada fila
        for row in range(1, min(max_row + 1, 50)):  # Limitar a 50 filas para rendimiento
            html += '<tr>'
            
            for col in range(1, min(max_col + 1, 20)):  # Limitar a 20 columnas
                cell = worksheet.cell(row=row, column=col)
                cell_value = str(cell.value) if cell.value is not None else ''
                
                # Aplicar estilos básicos
                cell_style = ''
                if cell.font and cell.font.bold:
                    cell_style += 'font-weight: bold; '
                if cell.fill and cell.fill.start_color.index != '00000000':
                    cell_style += f'background-color: {cell.fill.start_color.rgb}; '
                if cell.alignment and cell.alignment.horizontal == 'center':
                    cell_style += 'text-align: center; '
                elif cell.alignment and cell.alignment.horizontal == 'right':
                    cell_style += 'text-align: right; '
                
                # Determinar el tipo de celda
                if row == 1 or cell.font and cell.font.bold:
                    html += f'<th style="{cell_style}">{cell_value}</th>'
                else:
                    html += f'<td style="{cell_style}">{cell_value}</td>'
            
            html += '</tr>'
        
        html += '</table>'
        html += '</div>'
        
        # Información adicional
        html += '<div class="mt-3">'
        html += '<div class="alert alert-info">'
        html += '<h6><i class="fas fa-info-circle me-2"></i>Información del Contrato:</h6>'
        html += f'<ul class="mb-0">'
        html += f'<li><strong>Empleado:</strong> {contrato_generado.empleado.nombre_completo}</li>'
        html += f'<li><strong>Cédula:</strong> {contrato_generado.empleado.cedula}</li>'
        html += f'<li><strong>Cargo:</strong> {contrato_generado.empleado.cargo_puesto or "No especificado"}</li>'
        html += f'<li><strong>Salario:</strong> $ {contrato_generado.contrato.salario:,.0f}</li>'
        html += f'<li><strong>Tipo de Contrato:</strong> {contrato_generado.contrato.tipo_contrato}</li>'
        html += f'<li><strong>Fecha de Inicio:</strong> {contrato_generado.contrato.fecha_inicio.strftime("%d/%m/%Y")}</li>'
        if contrato_generado.contrato.fecha_fin:
            html += f'<li><strong>Fecha de Fin:</strong> {contrato_generado.contrato.fecha_fin.strftime("%d/%m/%Y")}</li>'
        else:
            html += f'<li><strong>Fecha de Fin:</strong> Indefinido</li>'
        html += f'</ul>'
        html += '</div>'
        html += '</div>'
        
        html += '</div>'
        
        return html
        
    except Exception as e:
        print(f"Error al convertir Excel a HTML: {str(e)}")
        return f'''
        <div class="alert alert-warning">
            <h6><i class="fas fa-exclamation-triangle me-2"></i>Error en Vista Previa</h6>
            <p>No se pudo generar la vista previa del contrato. Error: {str(e)}</p>
            <p>Puedes descargar el archivo Excel para verlo directamente.</p>
        </div>
        '''

app = Flask(__name__)

# Configuración de la aplicación
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_muy_segura_aqui')

# Registrar filtro de zona horaria para templates
@app.template_filter('colombia_time')
def colombia_time_filter(dt):
    """Filtro para convertir fechas a zona horaria de Colombia en templates"""
    return to_colombia_time(dt)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de base de datos
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Producción: usar PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"🔗 Usando PostgreSQL en producción")
else:
    # Verificar si estamos en producción (Railway, Heroku, etc.)
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DYNO') or os.environ.get('PORT'):
        # Estamos en producción pero no hay DATABASE_URL - ERROR
        raise RuntimeError(
            "❌ ERROR: DATABASE_URL no configurada en producción.\n"
            "💡 Solución: Agrega una base de datos PostgreSQL en Railway:\n"
            "   1. Ve a tu proyecto en Railway\n"
            "   2. Haz clic en '+ New' → 'Database' → 'PostgreSQL'\n"
            "   3. Railway configurará automáticamente DATABASE_URL"
        )
    else:
        # Desarrollo local: usar SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///empleados.db'
        print("💾 Usando SQLite para desarrollo local")

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelos de Base de Datos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)

class Empleado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Información Personal
    nombre_completo = db.Column(db.String(200), nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    genero = db.Column(db.String(20), nullable=False)  # Masculino, Femenino, Otro
    estado_civil = db.Column(db.String(30), nullable=False)  # Soltero, Casado, etc.
    
    # Contacto
    telefono_principal = db.Column(db.String(20), nullable=False)
    telefono_secundario = db.Column(db.String(20))
    email_personal = db.Column(db.String(120), nullable=False)
    email_corporativo = db.Column(db.String(120))
    
    # Dirección
    direccion_residencia = db.Column(db.Text, nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    departamento = db.Column(db.String(100), nullable=False)
    codigo_postal = db.Column(db.String(10))
    
    # Información Laboral
    cargo_puesto = db.Column(db.String(100), nullable=False)
    departamento_laboral = db.Column(db.String(50), nullable=False)  # Poscosecha, Cultivo, Administrativo, etc.
    fecha_ingreso = db.Column(db.Date, nullable=False)
    tipo_contrato = db.Column(db.String(30), nullable=False)  # Temporal, Indefinido, etc.
    salario_base = db.Column(db.Float, nullable=False)
    tipo_salario = db.Column(db.String(20), nullable=False)  # Mensual, Quincenal, etc.
    jornada_laboral = db.Column(db.String(30), nullable=False)  # Tiempo completo, Medio tiempo, etc.
    ubicacion_trabajo = db.Column(db.String(20), nullable=False)  # Oficina, Remoto, Híbrido
    estado_empleado = db.Column(db.String(20), nullable=False, default='Activo')  # Activo, Inactivo, Suspendido
    supervisor = db.Column(db.String(100))
    horario = db.Column(db.String(100))
    
    # Información de Seguridad Social
    eps = db.Column(db.String(100), nullable=False)
    arl = db.Column(db.String(100), nullable=False)
    afp = db.Column(db.String(100), nullable=False)
    caja_compensacion = db.Column(db.String(100))
    
    # Contacto de Emergencia
    nombre_contacto_emergencia = db.Column(db.String(200), nullable=False)
    telefono_emergencia = db.Column(db.String(20), nullable=False)
    parentesco = db.Column(db.String(50), nullable=False)
    
    # Campos del sistema
    created_at = db.Column(db.DateTime, default=colombia_now)
    updated_at = db.Column(db.DateTime, default=colombia_now, onupdate=colombia_now)

class Contrato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    tipo_contrato = db.Column(db.String(50), nullable=False)  # Temporal, Indefinido, etc.
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    salario = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=colombia_now)
    
    # Relación con Empleado
    empleado = db.relationship('Empleado', backref=db.backref('contratos', lazy=True))

class ContratoGenerado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contrato.id'), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    ruta_archivo = db.Column(db.String(500), nullable=False)
    archivo_data = db.Column(db.LargeBinary, nullable=True)  # Datos binarios del archivo
    fecha_generacion = db.Column(db.DateTime, default=colombia_now)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    empleado = db.relationship('Empleado', backref='contratos_generados')
    contrato = db.relationship('Contrato', backref='documentos_generados')

class Asistencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_entrada = db.Column(db.Time)
    hora_salida = db.Column(db.Time)
    horas_trabajadas = db.Column(db.Float)
    observaciones = db.Column(db.Text)
    token_diario = db.Column(db.String(100))  # Token del día para validación
    created_at = db.Column(db.DateTime, default=colombia_now)
    
    empleado = db.relationship('Empleado', backref=db.backref('asistencias', lazy=True))
    
    # Índice único para evitar asistencia duplicada por día
    __table_args__ = (db.UniqueConstraint('empleado_id', 'fecha', name='unique_attendance_per_day'),)

class Visitante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Información Personal
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(20), nullable=False)  # Cédula, pasaporte, etc.
    eps = db.Column(db.String(100), nullable=False)  # EPS del visitante
    rh = db.Column(db.String(10), nullable=False)  # Tipo de sangre
    
    # Contacto
    telefono = db.Column(db.String(20), nullable=False)
    empresa = db.Column(db.String(100))
    motivo_visita = db.Column(db.Text, nullable=False)
    
    # Control de Entrada/Salida
    fecha_entrada = db.Column(db.DateTime, default=colombia_now)
    fecha_salida = db.Column(db.DateTime)
    estado_visita = db.Column(db.String(20), default='En visita')  # En visita, Finalizada
    
    # Contacto de Emergencia
    nombre_contacto_emergencia = db.Column(db.String(200), nullable=False)
    telefono_emergencia = db.Column(db.String(20), nullable=False)
    parentesco = db.Column(db.String(50), nullable=False)
    
    # Campos del sistema
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=colombia_now)
    updated_at = db.Column(db.DateTime, default=colombia_now, onupdate=colombia_now)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Funciones para el sistema de QR y tokens
def generar_token_diario():
    """Genera un token único para el día actual que persiste 24 horas"""
    fecha_actual = date.today().strftime('%Y-%m-%d')
    # Usar una clave secreta fija para que el token sea consistente durante el día
    clave_secreta = "juancalito_sas_2024"
    token_base = f"{clave_secreta}_{fecha_actual}"
    return hashlib.sha256(token_base.encode()).hexdigest()[:32]

def validar_token_diario(token):
    """Valida si el token corresponde al día actual"""
    token_actual = generar_token_diario()
    return token == token_actual

def generar_token_diario_visitantes():
    """Genera un token único para visitantes del día actual que persiste 24 horas"""
    fecha_actual = date.today().strftime('%Y-%m-%d')
    # Usar una clave secreta diferente para visitantes
    clave_secreta = "juancalito_visitantes_2024"
    token_base = f"{clave_secreta}_{fecha_actual}"
    return hashlib.sha256(token_base.encode()).hexdigest()[:32]

def validar_token_diario_visitantes(token):
    """Valida si el token de visitantes corresponde al día actual"""
    token_actual = generar_token_diario_visitantes()
    return token == token_actual

def generar_qr_asistencia():
    """Genera un código QR para la asistencia del día"""
    token = generar_token_diario()
    url_asistencia = f"{request.url_root}asistencia-publica/{token}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_asistencia)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar en memoria
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer, token, url_asistencia

def generar_qr_visitantes():
    """Genera un código QR para el registro de visitantes del día"""
    token = generar_token_diario_visitantes()
    url_visitantes = f"{request.url_root}visitantes-publico/{token}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_visitantes)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar en memoria
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer, token, url_visitantes

# Rutas de Autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Email o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboard Principal
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    # Estadísticas para el dashboard
    total_empleados = Empleado.query.filter_by(estado_empleado='Activo').count()
    total_visitantes_hoy = Visitante.query.filter(
        Visitante.fecha_entrada >= datetime.now().date(),
        Visitante.activo == True
    ).count()
    
    # Empleados con asistencia hoy
    asistencias_hoy = Asistencia.query.filter_by(fecha=date.today()).count()
    
    # Contratos próximos a vencer (próximos 30 días)
    contratos_vencer = Contrato.query.filter(
        Contrato.fecha_fin <= date.today() + timedelta(days=30),
        Contrato.activo == True
    ).count()
    
    return render_template('dashboard.html', 
                         total_empleados=total_empleados,
                         total_visitantes_hoy=total_visitantes_hoy,
                         asistencias_hoy=asistencias_hoy,
                         contratos_vencer=contratos_vencer)

# Gestión de Empleados
@app.route('/empleados')
@login_required
def empleados():
    empleados = Empleado.query.filter_by(estado_empleado='Activo').all()
    return render_template('empleados.html', empleados=empleados)

@app.route('/empleados/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_empleado():
    if request.method == 'POST':
        empleado = Empleado(
            # Información Personal
            nombre_completo=request.form['nombre_completo'],
            cedula=request.form['cedula'],
            fecha_nacimiento=datetime.strptime(request.form['fecha_nacimiento'], '%Y-%m-%d').date(),
            genero=request.form['genero'],
            estado_civil=request.form['estado_civil'],
            
            # Contacto
            telefono_principal=request.form['telefono_principal'],
            telefono_secundario=request.form.get('telefono_secundario', ''),
            email_personal=request.form['email_personal'],
            email_corporativo=request.form.get('email_corporativo', ''),
            
            # Dirección
            direccion_residencia=request.form['direccion_residencia'],
            ciudad=request.form['ciudad'],
            departamento=request.form['departamento'],
            codigo_postal=request.form.get('codigo_postal', ''),
            
            # Información Laboral
            cargo_puesto=request.form['cargo_puesto'],
            departamento_laboral=request.form['departamento_laboral'],
            fecha_ingreso=datetime.strptime(request.form['fecha_ingreso'], '%Y-%m-%d').date(),
            tipo_contrato=request.form['tipo_contrato'],
            salario_base=float(request.form['salario_base']),
            tipo_salario=request.form['tipo_salario'],
            jornada_laboral=request.form['jornada_laboral'],
            ubicacion_trabajo=request.form['ubicacion_trabajo'],
            estado_empleado=request.form['estado_empleado'],
            supervisor=request.form.get('supervisor', ''),
            horario=request.form.get('horario', ''),
            
            # Seguridad Social
            eps=request.form['eps'],
            arl=request.form['arl'],
            afp=request.form['afp'],
            caja_compensacion=request.form.get('caja_compensacion', ''),
            
            # Contacto de Emergencia
            nombre_contacto_emergencia=request.form['nombre_contacto_emergencia'],
            telefono_emergencia=request.form['telefono_emergencia'],
            parentesco=request.form['parentesco']
        )
        db.session.add(empleado)
        db.session.commit()
        flash('Empleado creado exitosamente', 'success')
        return redirect(url_for('empleados'))
    
    return render_template('nuevo_empleado.html')

@app.route('/empleados/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_empleado(id):
    empleado = Empleado.query.get_or_404(id)
    
    if request.method == 'POST':
        # Información Personal
        empleado.nombre_completo = request.form['nombre_completo']
        empleado.cedula = request.form['cedula']
        empleado.fecha_nacimiento = datetime.strptime(request.form['fecha_nacimiento'], '%Y-%m-%d').date()
        empleado.genero = request.form['genero']
        empleado.estado_civil = request.form['estado_civil']
        
        # Contacto
        empleado.telefono_principal = request.form['telefono_principal']
        empleado.telefono_secundario = request.form.get('telefono_secundario', '')
        empleado.email_personal = request.form['email_personal']
        empleado.email_corporativo = request.form.get('email_corporativo', '')
        
        # Dirección
        empleado.direccion_residencia = request.form['direccion_residencia']
        empleado.ciudad = request.form['ciudad']
        empleado.departamento = request.form['departamento']
        empleado.codigo_postal = request.form.get('codigo_postal', '')
        
        # Información Laboral
        empleado.cargo_puesto = request.form['cargo_puesto']
        empleado.departamento_laboral = request.form['departamento_laboral']
        empleado.fecha_ingreso = datetime.strptime(request.form['fecha_ingreso'], '%Y-%m-%d').date()
        empleado.tipo_contrato = request.form['tipo_contrato']
        empleado.salario_base = float(request.form['salario_base'])
        empleado.tipo_salario = request.form['tipo_salario']
        empleado.jornada_laboral = request.form['jornada_laboral']
        empleado.ubicacion_trabajo = request.form['ubicacion_trabajo']
        empleado.estado_empleado = request.form['estado_empleado']
        empleado.supervisor = request.form.get('supervisor', '')
        empleado.horario = request.form.get('horario', '')
        
        # Seguridad Social
        empleado.eps = request.form['eps']
        empleado.arl = request.form['arl']
        empleado.afp = request.form['afp']
        empleado.caja_compensacion = request.form.get('caja_compensacion', '')
        
        # Contacto de Emergencia
        empleado.nombre_contacto_emergencia = request.form['nombre_contacto_emergencia']
        empleado.telefono_emergencia = request.form['telefono_emergencia']
        empleado.parentesco = request.form['parentesco']
        
        db.session.commit()
        flash('Empleado actualizado exitosamente', 'success')
        return redirect(url_for('empleados'))
    
    return render_template('editar_empleado.html', empleado=empleado)

@app.route('/empleados/<int:id>')
@login_required
def ver_empleado(id):
    empleado = Empleado.query.get_or_404(id)
    return render_template('ver_empleado.html', empleado=empleado)

@app.route('/empleados/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_empleado(id):
    empleado = Empleado.query.get_or_404(id)
    empleado.estado_empleado = 'Inactivo'
    db.session.commit()
    flash('Empleado desactivado exitosamente', 'success')
    return redirect(url_for('empleados'))

# Gestión de Contratos - Rutas movidas a la sección completa más abajo

# Gestión de Asistencia
@app.route('/asistencia')
@login_required
def asistencia():
    fecha = request.args.get('fecha', date.today().strftime('%Y-%m-%d'))
    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    
    asistencias = Asistencia.query.filter_by(fecha=fecha_obj).all()
    empleados = Empleado.query.filter_by(estado_empleado='Activo').all()
    
    # Generar QR para el día actual
    qr_buffer, token, url_qr = generar_qr_asistencia()
    
    return render_template('asistencia.html', 
                         asistencias=asistencias, 
                         empleados=empleados, 
                         fecha=fecha,
                         token_diario=token,
                         url_qr=url_qr)

@app.route('/asistencia/qr')
@login_required
def generar_qr_imagen():
    """Genera y devuelve la imagen del código QR"""
    qr_buffer, token, url_qr = generar_qr_asistencia()
    return send_file(qr_buffer, mimetype='image/png')

@app.route('/visitantes/qr')
@login_required
def generar_qr_visitantes_imagen():
    """Genera y devuelve la imagen del código QR para visitantes"""
    qr_buffer, token, url_qr = generar_qr_visitantes()
    return send_file(qr_buffer, mimetype='image/png')

# Ruta pública para asistencia (sin login requerido)
@app.route('/asistencia-publica/<token>', methods=['GET', 'POST'])
def asistencia_publica(token):
    """Página pública para que los empleados marquen asistencia"""
    # Validar que el token sea del día actual
    if not validar_token_diario(token):
        flash('El código QR ha expirado. Solicite un nuevo código al administrador.', 'error')
        return render_template('asistencia_publica.html', token=token, error=True)
    
    if request.method == 'POST':
        documento = request.form.get('documento', '').strip()
        nombre = request.form.get('nombre', '').strip()
        tipo_registro = request.form.get('tipo_registro', '').strip()
        
        if not documento or not nombre or not tipo_registro:
            flash('Por favor complete todos los campos y seleccione el tipo de registro', 'error')
            return render_template('asistencia_publica.html', token=token)
        
        # Buscar empleado por documento
        empleado = Empleado.query.filter_by(cedula=documento).first()
        
        if not empleado:
            flash('No se encontró un empleado con ese documento', 'error')
            return render_template('asistencia_publica.html', token=token)
        
        # Verificar que el nombre coincida (validación más flexible)
        nombre_empleado = empleado.nombre_completo.lower().strip()
        nombre_ingresado = nombre.lower().strip()
        
        # Permitir coincidencias parciales y diferentes formatos
        if not (nombre_empleado == nombre_ingresado or 
                nombre_empleado in nombre_ingresado or 
                nombre_ingresado in nombre_empleado):
            flash(f'El nombre ingresado no coincide con el empleado registrado. Empleado: {empleado.nombre_completo}', 'error')
            return render_template('asistencia_publica.html', token=token)
        
        # Verificar que el empleado esté activo
        if empleado.estado_empleado != 'Activo':
            flash('El empleado no está activo en el sistema', 'error')
            return render_template('asistencia_publica.html', token=token)
        
        fecha_hoy = date.today()
        hora_actual = datetime.now().time()
        
        # Buscar asistencia existente para hoy
        asistencia_existente = Asistencia.query.filter_by(
            empleado_id=empleado.id, 
            fecha=fecha_hoy
        ).first()
        
        if tipo_registro == 'entrada':
            if asistencia_existente:
                flash(f'Ya se registró entrada para {empleado.nombre_completo} hoy a las {asistencia_existente.hora_entrada.strftime("%H:%M")}', 'warning')
                return render_template('asistencia_publica.html', token=token)
            
            # Registrar entrada
            asistencia = Asistencia(
                empleado_id=empleado.id,
                fecha=fecha_hoy,
                hora_entrada=hora_actual,
                token_diario=token
            )
            
            try:
                db.session.add(asistencia)
                db.session.commit()
                flash(f'Entrada registrada exitosamente para {empleado.nombre_completo} a las {colombia_now().strftime("%H:%M")}', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error al registrar la entrada. Intente nuevamente.', 'error')
        
        elif tipo_registro == 'salida':
            if not asistencia_existente:
                flash(f'No se encontró registro de entrada para {empleado.nombre_completo} hoy. Debe registrar entrada primero.', 'error')
                return render_template('asistencia_publica.html', token=token)
            
            if asistencia_existente.hora_salida:
                flash(f'Ya se registró salida para {empleado.nombre_completo} hoy a las {asistencia_existente.hora_salida.strftime("%H:%M")}', 'warning')
                return render_template('asistencia_publica.html', token=token)
            
            # Registrar salida
            asistencia_existente.hora_salida = hora_actual
            asistencia_existente.token_diario = token
            
            try:
                db.session.commit()
                flash(f'Salida registrada exitosamente para {empleado.nombre_completo} a las {colombia_now().strftime("%H:%M")}', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error al registrar la salida. Intente nuevamente.', 'error')
        
        return render_template('asistencia_publica.html', token=token)
    
    return render_template('asistencia_publica.html', token=token)

# Ruta pública para visitantes (sin login requerido)
@app.route('/visitantes-publico/<token>', methods=['GET', 'POST'])
def visitantes_publico(token):
    """Página pública para que los visitantes se registren"""
    # Validar que el token sea del día actual
    if not validar_token_diario_visitantes(token):
        flash('El código QR ha expirado. Solicite un nuevo código al administrador.', 'error')
        return render_template('visitantes_publico.html', token=token, error=True)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        documento = request.form.get('documento', '').strip()
        eps = request.form.get('eps', '').strip()
        rh = request.form.get('rh', '').strip()
        telefono = request.form.get('telefono', '').strip()
        empresa = request.form.get('empresa', '').strip()
        motivo_visita = request.form.get('motivo_visita', '').strip()
        nombre_contacto_emergencia = request.form.get('nombre_contacto_emergencia', '').strip()
        telefono_emergencia = request.form.get('telefono_emergencia', '').strip()
        parentesco = request.form.get('parentesco', '').strip()
        
        # Validar campos requeridos
        campos_requeridos = {
            'nombre': nombre,
            'apellido': apellido,
            'documento': documento,
            'eps': eps,
            'rh': rh,
            'telefono': telefono,
            'empresa': empresa,
            'motivo_visita': motivo_visita,
            'nombre_contacto_emergencia': nombre_contacto_emergencia,
            'telefono_emergencia': telefono_emergencia,
            'parentesco': parentesco
        }
        
        campos_faltantes = [campo for campo, valor in campos_requeridos.items() if not valor]
        if campos_faltantes:
            flash('Por favor complete todos los campos requeridos', 'error')
            return render_template('visitantes_publico.html', token=token)
        
        # Verificar si ya existe un visitante con el mismo documento hoy
        fecha_hoy = date.today()
        visitante_existente = Visitante.query.filter(
            Visitante.documento == documento,
            db.func.date(Visitante.fecha_entrada) == fecha_hoy
        ).first()
        
        if visitante_existente:
            flash(f'Ya existe un registro de visitante con documento {documento} para hoy', 'warning')
            return render_template('visitantes_publico.html', token=token)
        
        # Crear nuevo visitante
        visitante = Visitante(
            nombre=nombre,
            apellido=apellido,
            documento=documento,
            eps=eps,
            rh=rh,
            telefono=telefono,
            empresa=empresa,
            motivo_visita=motivo_visita,
            fecha_entrada=datetime.now(),
            estado_visita='En visita',
            nombre_contacto_emergencia=nombre_contacto_emergencia,
            telefono_emergencia=telefono_emergencia,
            parentesco=parentesco,
            activo=True
        )
        
        try:
            db.session.add(visitante)
            db.session.commit()
            flash(f'Visitante {nombre} {apellido} registrado exitosamente a las {colombia_now().strftime("%H:%M")}', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar el visitante. Intente nuevamente.', 'error')
        
        return render_template('visitantes_publico.html', token=token)
    
    return render_template('visitantes_publico.html', token=token)

@app.route('/asistencia/registrar', methods=['POST'])
@login_required
def registrar_asistencia():
    empleado_id = request.form['empleado_id']
    fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
    tipo_registro = request.form.get('tipo_registro', '').strip()
    observaciones = request.form.get('observaciones', '')
    
    if not tipo_registro:
        flash('Por favor seleccione el tipo de registro (entrada o salida)', 'error')
        return redirect(url_for('asistencia'))
    
    # Buscar empleado
    empleado = Empleado.query.get(empleado_id)
    if not empleado:
        flash('Empleado no encontrado', 'error')
        return redirect(url_for('asistencia'))
    
    # Buscar asistencia existente para hoy
    asistencia_existente = Asistencia.query.filter_by(
        empleado_id=empleado_id, 
        fecha=fecha
    ).first()
    
    if tipo_registro == 'entrada':
        if asistencia_existente:
            flash(f'Ya se registró entrada para {empleado.nombre_completo} hoy a las {asistencia_existente.hora_entrada.strftime("%H:%M")}', 'warning')
            return redirect(url_for('asistencia'))
        
        # Registrar entrada
        asistencia = Asistencia(
            empleado_id=empleado_id,
            fecha=fecha,
            hora_entrada=datetime.now().time(),
            observaciones=observaciones,
            token_diario='Manual'  # Marcar como registro manual
        )
        
        try:
            db.session.add(asistencia)
            db.session.commit()
            flash(f'Entrada registrada exitosamente para {empleado.nombre_completo} a las {colombia_now().strftime("%H:%M")}', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar la entrada. Intente nuevamente.', 'error')
    
    elif tipo_registro == 'salida':
        if not asistencia_existente:
            flash(f'No se encontró registro de entrada para {empleado.nombre_completo} hoy. Debe registrar entrada primero.', 'error')
            return redirect(url_for('asistencia'))
        
        if asistencia_existente.hora_salida:
            flash(f'Ya se registró salida para {empleado.nombre_completo} hoy a las {asistencia_existente.hora_salida.strftime("%H:%M")}', 'warning')
            return redirect(url_for('asistencia'))
        
        # Registrar salida
        hora_salida = datetime.now().time()
        asistencia_existente.hora_salida = hora_salida
        
        # Calcular horas trabajadas
        entrada = datetime.combine(fecha, asistencia_existente.hora_entrada)
        salida = datetime.combine(fecha, hora_salida)
        asistencia_existente.horas_trabajadas = (salida - entrada).total_seconds() / 3600
        
        # Actualizar observaciones si se proporcionaron
        if observaciones:
            asistencia_existente.observaciones = observaciones
        
        try:
            db.session.commit()
            flash(f'Salida registrada exitosamente para {empleado.nombre_completo} a las {colombia_now().strftime("%H:%M")}', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar la salida. Intente nuevamente.', 'error')
    
    return redirect(url_for('asistencia'))

@app.route('/asistencia/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_asistencia(id):
    """Eliminar una asistencia (solo si no tiene salida registrada)"""
    try:
        asistencia = Asistencia.query.get_or_404(id)
        
        # Solo permitir eliminar si no tiene salida registrada
        if asistencia.hora_salida:
            return jsonify({
                'success': False,
                'message': 'No se puede eliminar una asistencia que ya tiene salida registrada'
            }), 400
        
        db.session.delete(asistencia)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Asistencia eliminada exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al eliminar la asistencia: {str(e)}'
        }), 500

# Gestión de Visitantes
@app.route('/visitantes')
@login_required
def visitantes():
    visitantes = Visitante.query.order_by(Visitante.created_at.desc()).all()
    
    # Generar QR para visitantes
    qr_buffer, token, url_qr = generar_qr_visitantes()
    
    return render_template('visitantes.html', 
                         visitantes=visitantes,
                         token_diario=token,
                         url_qr=url_qr)

@app.route('/visitantes/detalles/<int:id>')
@login_required
def detalles_visitante(id):
    visitante = Visitante.query.get_or_404(id)
    return render_template('detalles_visitante.html', visitante=visitante)

@app.route('/asistencia/detalles/<int:id>')
@login_required
def detalles_asistencia(id):
    asistencia = Asistencia.query.get_or_404(id)
    return render_template('detalles_asistencia.html', asistencia=asistencia)

# ===== RUTAS PARA CONTRATOS =====

@app.route('/contratos')
@login_required
def contratos():
    """Lista todos los contratos con opciones CRUD"""
    contratos = Contrato.query.join(Empleado).order_by(Contrato.created_at.desc()).all()
    return render_template('contratos.html', contratos=contratos)

@app.route('/contratos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_contrato():
    """Crear nuevo contrato"""
    if request.method == 'POST':
        contrato = Contrato(
            empleado_id=request.form['empleado_id'],
            tipo_contrato=request.form['tipo_contrato'],
            fecha_inicio=datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d').date(),
            fecha_fin=datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d').date() if request.form.get('fecha_fin') else None,
            salario=float(request.form['salario']),
            descripcion=request.form.get('descripcion', '')
        )
        db.session.add(contrato)
        db.session.commit()
        flash('Contrato creado exitosamente', 'success')
        return redirect(url_for('contratos'))
    
    empleados = Empleado.query.filter_by(estado_empleado='Activo').all()
    return render_template('nuevo_contrato.html', empleados=empleados)

@app.route('/contratos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_contrato(id):
    """Editar contrato existente"""
    contrato = Contrato.query.get_or_404(id)
    
    if request.method == 'POST':
        contrato.empleado_id = request.form['empleado_id']
        contrato.tipo_contrato = request.form['tipo_contrato']
        contrato.fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d').date()
        contrato.fecha_fin = datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d').date() if request.form.get('fecha_fin') else None
        contrato.salario = float(request.form['salario'])
        contrato.descripcion = request.form.get('descripcion', '')
        
        db.session.commit()
        flash('Contrato actualizado exitosamente', 'success')
        return redirect(url_for('contratos'))
    
    empleados = Empleado.query.filter_by(estado_empleado='Activo').all()
    return render_template('editar_contrato.html', contrato=contrato, empleados=empleados)

@app.route('/contratos/desactivar/<int:id>')
@login_required
def desactivar_contrato(id):
    """Desactivar contrato"""
    contrato = Contrato.query.get_or_404(id)
    contrato.activo = False
    db.session.commit()
    flash('Contrato desactivado exitosamente', 'success')
    return redirect(url_for('contratos'))

@app.route('/contratos/activar/<int:id>')
@login_required
def activar_contrato(id):
    """Activar contrato"""
    contrato = Contrato.query.get_or_404(id)
    contrato.activo = True
    db.session.commit()
    flash('Contrato activado exitosamente', 'success')
    return redirect(url_for('contratos'))

@app.route('/contratos/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_contrato(id):
    """Eliminar contrato"""
    try:
        contrato = Contrato.query.get_or_404(id)
        db.session.delete(contrato)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Contrato eliminado exitosamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al eliminar el contrato: {str(e)}'
        }), 500

@app.route('/contratos/generar/<int:id>')
@login_required
def generar_contrato(id):
    """Generar contrato Excel con control de duplicados"""
    try:
        # Verificar si ya existe un contrato generado para este empleado
        contrato = Contrato.query.get_or_404(id)
        empleado_id = contrato.empleado_id
        
        # Buscar contratos generados existentes para este empleado
        contrato_existente = ContratoGenerado.query.filter_by(empleado_id=empleado_id).first()
        
        if contrato_existente:
            # Si ya existe, preguntar si quiere regenerar
            flash(f'Ya existe un contrato generado para {contrato.empleado.nombre_completo}. Usa "Regenerar" para crear uno nuevo.', 'warning')
            return redirect(url_for('contratos_generados'))
        
        # Si no existe, generar nuevo contrato
        contrato_generado = generar_contrato_excel(id)
        flash(f'Contrato generado exitosamente: {contrato_generado.nombre_archivo}', 'success')
        return redirect(url_for('contratos'))
        
    except Exception as e:
        flash(f'Error al generar el contrato: {str(e)}', 'error')
        return redirect(url_for('contratos'))

@app.route('/contratos/generados')
@login_required
def contratos_generados():
    """Lista de contratos generados"""
    try:
        # Intentar crear la tabla si no existe
        try:
            with db.engine.connect() as connection:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS contrato_generado (
                        id SERIAL PRIMARY KEY,
                        empleado_id INTEGER NOT NULL REFERENCES empleado(id),
                        contrato_id INTEGER NOT NULL REFERENCES contrato(id),
                        nombre_archivo VARCHAR(255) NOT NULL,
                        ruta_archivo VARCHAR(500) NOT NULL,
                        fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        activo BOOLEAN DEFAULT TRUE
                    );
                """))
                connection.commit()
            print("✅ Tabla contrato_generado creada/verificada")
        except Exception as create_error:
            print(f"⚠️ No se pudo crear la tabla: {create_error}")
        
        contratos_generados = ContratoGenerado.query.join(Empleado).join(Contrato).order_by(ContratoGenerado.fecha_generacion.desc()).all()
        return render_template('contratos_generados.html', contratos_generados=contratos_generados)
    except Exception as e:
        print(f"Error al cargar contratos generados: {str(e)}")
        flash('Error al cargar contratos generados. La tabla puede no existir aún.', 'error')
        return render_template('contratos_generados.html', contratos_generados=[])

@app.route('/contratos/descargar/<int:id>')
@login_required
def descargar_contrato(id):
    """Descargar contrato generado"""
    contrato_generado = ContratoGenerado.query.get_or_404(id)
    
    # Verificar si tenemos datos binarios en la base de datos
    if contrato_generado.archivo_data:
        # Crear respuesta desde datos binarios
        from io import BytesIO
        return send_file(
            BytesIO(contrato_generado.archivo_data),
            as_attachment=True,
            download_name=contrato_generado.nombre_archivo,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        # Fallback: intentar desde archivo (para contratos antiguos)
        if os.path.exists(contrato_generado.ruta_archivo):
            return send_file(
                contrato_generado.ruta_archivo,
                as_attachment=True,
                download_name=contrato_generado.nombre_archivo,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            flash('El archivo del contrato no existe', 'error')
            return redirect(url_for('contratos_generados'))

@app.route('/contratos/regenerar/<int:id>')
@login_required
def regenerar_contrato(id):
    """Regenerar contrato (eliminar el anterior y crear uno nuevo)"""
    try:
        # Intentar crear la tabla si no existe
        try:
            with db.engine.connect() as connection:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS contrato_generado (
                        id SERIAL PRIMARY KEY,
                        empleado_id INTEGER NOT NULL REFERENCES empleado(id),
                        contrato_id INTEGER NOT NULL REFERENCES contrato(id),
                        nombre_archivo VARCHAR(255) NOT NULL,
                        ruta_archivo VARCHAR(500) NOT NULL,
                        fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        activo BOOLEAN DEFAULT TRUE
                    );
                """))
                connection.commit()
            print("✅ Tabla contrato_generado creada/verificada en regenerar")
        except Exception as create_error:
            print(f"⚠️ No se pudo crear la tabla en regenerar: {create_error}")
        
        # Obtener el contrato generado actual
        contrato_generado = ContratoGenerado.query.get_or_404(id)
        contrato_id = contrato_generado.contrato_id
        empleado_nombre = contrato_generado.empleado.nombre_completo
        
        # Eliminar el archivo anterior si existe
        if os.path.exists(contrato_generado.ruta_archivo):
            os.remove(contrato_generado.ruta_archivo)
            print(f"✅ Archivo anterior eliminado: {contrato_generado.ruta_archivo}")
        
        # Eliminar el registro de la base de datos
        db.session.delete(contrato_generado)
        db.session.commit()
        print(f"✅ Registro anterior eliminado de la base de datos")
        
        # Generar nuevo contrato
        nuevo_contrato = generar_contrato_excel(contrato_id)
        
        flash(f'Contrato regenerado exitosamente para {empleado_nombre}', 'success')
        return redirect(url_for('contratos_generados'))
        
    except Exception as e:
        print(f"Error al regenerar contrato: {str(e)}")
        flash(f'Error al regenerar el contrato: {str(e)}', 'error')
        return redirect(url_for('contratos_generados'))

@app.route('/contratos/vista_previa/<int:id>')
@login_required
def vista_previa_contrato(id):
    """Vista previa del contrato generado"""
    try:
        contrato_generado = ContratoGenerado.query.get_or_404(id)
        
        # Verificar si tenemos datos binarios en la base de datos
        if contrato_generado.archivo_data:
            # Leer desde datos binarios
            from io import BytesIO
            workbook = openpyxl.load_workbook(BytesIO(contrato_generado.archivo_data))
        else:
            # Fallback: intentar desde archivo (para contratos antiguos)
            if not os.path.exists(contrato_generado.ruta_archivo):
                return jsonify({
                    'success': False,
                    'message': 'El archivo del contrato no existe'
                }), 404
            
            # Leer el archivo Excel
            workbook = openpyxl.load_workbook(contrato_generado.ruta_archivo)
        
        worksheet = workbook.active
        
        # Convertir a HTML
        html_content = convertir_excel_a_html(worksheet, contrato_generado)
        
        return jsonify({
            'success': True,
            'html': html_content,
            'empleado': contrato_generado.empleado.nombre_completo,
            'fecha': contrato_generado.fecha_generacion.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        print(f"Error al generar vista previa: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al generar vista previa: {str(e)}'
        }), 500

@app.route('/contratos/eliminar_generado/<int:id>', methods=['DELETE', 'POST'])
@login_required
def eliminar_contrato_generado(id):
    """Eliminar contrato generado"""
    try:
        # Intentar crear la tabla si no existe
        try:
            with db.engine.connect() as connection:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS contrato_generado (
                        id SERIAL PRIMARY KEY,
                        empleado_id INTEGER NOT NULL REFERENCES empleado(id),
                        contrato_id INTEGER NOT NULL REFERENCES contrato(id),
                        nombre_archivo VARCHAR(255) NOT NULL,
                        ruta_archivo VARCHAR(500) NOT NULL,
                        fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        activo BOOLEAN DEFAULT TRUE
                    );
                """))
                connection.commit()
            print("✅ Tabla contrato_generado creada/verificada en eliminar")
        except Exception as create_error:
            print(f"⚠️ No se pudo crear la tabla en eliminar: {create_error}")
        
        contrato_generado = ContratoGenerado.query.get_or_404(id)
        empleado_nombre = contrato_generado.empleado.nombre_completo
        
        # Eliminar el archivo si existe (para contratos antiguos)
        if os.path.exists(contrato_generado.ruta_archivo):
            os.remove(contrato_generado.ruta_archivo)
            print(f"✅ Archivo eliminado: {contrato_generado.ruta_archivo}")
        
        # Eliminar el registro de la base de datos (incluye datos binarios)
        db.session.delete(contrato_generado)
        db.session.commit()
        
        # Si es una petición AJAX, devolver JSON
        if request.headers.get('Content-Type') == 'application/json' or request.method == 'DELETE':
            return jsonify({
                'success': True,
                'message': f'Contrato de {empleado_nombre} eliminado exitosamente'
            })
        else:
            # Si es una petición normal, redirigir
            flash(f'Contrato de {empleado_nombre} eliminado exitosamente', 'success')
            return redirect(url_for('contratos_generados'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar contrato generado: {str(e)}")
        
        # Si es una petición AJAX, devolver JSON
        if request.headers.get('Content-Type') == 'application/json' or request.method == 'DELETE':
            return jsonify({
                'success': False,
                'message': f'Error al eliminar el contrato: {str(e)}'
            }), 500
        else:
            # Si es una petición normal, redirigir con error
            flash(f'Error al eliminar contrato: {str(e)}', 'error')
            return redirect(url_for('contratos_generados'))

@app.route('/visitantes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_visitante():
    if request.method == 'POST':
        visitante = Visitante(
            nombre=request.form['nombre'],
            apellido=request.form['apellido'],
            documento=request.form['documento'],
            eps=request.form['eps'],
            rh=request.form['rh'],
            telefono=request.form['telefono'],
            empresa=request.form.get('empresa', ''),
            motivo_visita=request.form['motivo_visita'],
            nombre_contacto_emergencia=request.form['nombre_contacto_emergencia'],
            telefono_emergencia=request.form['telefono_emergencia'],
            parentesco=request.form['parentesco'],
            estado_visita='Pendiente',  # Estado inicial - esperando entrada
            activo=False  # No activo hasta que se registre la entrada
        )
        db.session.add(visitante)
        db.session.commit()
        flash('Visitante registrado exitosamente. Use el botón de Entrada/Salida para registrar su llegada.', 'success')
        return redirect(url_for('visitantes'))
    
    return render_template('nuevo_visitante.html')

@app.route('/visitantes/<int:id>/entrada-salida', methods=['POST'])
@login_required
def registrar_entrada_salida_visitante(id):
    visitante = Visitante.query.get_or_404(id)
    
    if visitante.estado_visita == 'En visita':
        # Registrar salida
        visitante.fecha_salida = colombia_now()
        visitante.estado_visita = 'Finalizada'
        visitante.activo = False
        db.session.commit()
        flash(f'Salida registrada para {visitante.nombre} {visitante.apellido} a las {visitante.fecha_salida.strftime("%H:%M")}', 'success')
    else:
        # Registrar entrada (nuevo visitante)
        visitante.fecha_entrada = colombia_now()
        visitante.estado_visita = 'En visita'
        visitante.activo = True
        visitante.fecha_salida = None
        db.session.commit()
        flash(f'Entrada registrada para {visitante.nombre} {visitante.apellido} a las {visitante.fecha_entrada.strftime("%H:%M")}', 'success')
    
    return redirect(url_for('visitantes'))

# Reportes
@app.route('/reportes')
@login_required
def reportes():
    return render_template('reportes.html')

@app.route('/reportes/asistencia')
@login_required
def reporte_asistencia():
    fecha_inicio = request.args.get('fecha_inicio', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_fin = request.args.get('fecha_fin', date.today().strftime('%Y-%m-%d'))
    
    asistencias = Asistencia.query.filter(
        Asistencia.fecha >= datetime.strptime(fecha_inicio, '%Y-%m-%d').date(),
        Asistencia.fecha <= datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    ).all()
    
    return render_template('reporte_asistencia.html', asistencias=asistencias, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

@app.route('/reportes/empleados')
@login_required
def reporte_empleados():
    empleados = Empleado.query.filter_by(estado_empleado='Activo').all()
    return render_template('reporte_empleados.html', empleados=empleados)

@app.route('/reportes/visitantes')
@login_required
def reporte_visitantes():
    fecha_inicio = request.args.get('fecha_inicio', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_fin = request.args.get('fecha_fin', date.today().strftime('%Y-%m-%d'))
    
    visitantes = Visitante.query.filter(
        Visitante.fecha_entrada >= datetime.strptime(fecha_inicio, '%Y-%m-%d').date(),
        Visitante.fecha_entrada <= datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    ).all()
    
    return render_template('reporte_visitantes.html', visitantes=visitantes, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

# Inicialización de la base de datos
def init_db():
    try:
        with app.app_context():
            print("📊 Creando tablas de la base de datos...")
            db.create_all()
            
            # Crear usuario administrador por defecto
            admin_user = User.query.filter_by(email='admin@juancalito.com').first()
            if not admin_user:
                admin_user = User(
                    email='admin@juancalito.com',
                    username='Administrador',
                    password_hash=generate_password_hash('nueva_contraseña_2024'),
                    is_admin=True
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Usuario administrador creado: admin@juancalito.com / nueva_contraseña_2024")
            else:
                print("✅ Usuario administrador ya existe")
            
            print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        print("🚀 Iniciando aplicación...")
        init_db()
        port = int(os.environ.get('PORT', 5000))
        print(f"🌐 Servidor iniciado en puerto {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {str(e)}")
        raise
