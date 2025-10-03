from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import os
import qrcode
import io
import hashlib
import secrets
from config import config

app = Flask(__name__)

# Configuración basada en entorno
config_name = os.environ.get('FLASK_ENV', 'production')
app.config.from_object(config[config_name])
config[config_name].init_app(app)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Contrato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    tipo_contrato = db.Column(db.String(50), nullable=False)  # Temporal, Indefinido, etc.
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    salario = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    empleado = db.relationship('Empleado', backref=db.backref('contratos', lazy=True))

class Asistencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_entrada = db.Column(db.Time)
    hora_salida = db.Column(db.Time)
    horas_trabajadas = db.Column(db.Float)
    observaciones = db.Column(db.Text)
    token_diario = db.Column(db.String(100))  # Token del día para validación
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    fecha_entrada = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_salida = db.Column(db.DateTime)
    estado_visita = db.Column(db.String(20), default='En visita')  # En visita, Finalizada
    
    # Contacto de Emergencia
    nombre_contacto_emergencia = db.Column(db.String(200), nullable=False)
    telefono_emergencia = db.Column(db.String(20), nullable=False)
    parentesco = db.Column(db.String(50), nullable=False)
    
    # Campos del sistema
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

# Gestión de Contratos
@app.route('/contratos')
@login_required
def contratos():
    contratos = Contrato.query.filter_by(activo=True).all()
    return render_template('contratos.html', contratos=contratos)

@app.route('/contratos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_contrato():
    if request.method == 'POST':
        contrato = Contrato(
            empleado_id=int(request.form['empleado_id']),
            tipo_contrato=request.form['tipo_contrato'],
            fecha_inicio=datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d').date(),
            fecha_fin=datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d').date() if request.form['fecha_fin'] else None,
            salario=float(request.form['salario']),
            descripcion=request.form['descripcion']
        )
        db.session.add(contrato)
        db.session.commit()
        flash('Contrato creado exitosamente', 'success')
        return redirect(url_for('contratos'))
    
    empleados = Empleado.query.filter_by(estado_empleado='Activo').all()
    return render_template('nuevo_contrato.html', empleados=empleados)

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
        
        # Verificar que el nombre coincida (insensible a mayúsculas)
        if empleado.nombre_completo.lower() != nombre.lower():
            flash('El nombre no coincide con el empleado registrado', 'error')
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
                flash(f'Entrada registrada exitosamente para {empleado.nombre_completo} a las {hora_actual.strftime("%H:%M")}', 'success')
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
                flash(f'Salida registrada exitosamente para {empleado.nombre_completo} a las {hora_actual.strftime("%H:%M")}', 'success')
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
            flash(f'Visitante {nombre} {apellido} registrado exitosamente a las {datetime.now().strftime("%H:%M")}', 'success')
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
            flash(f'Entrada registrada exitosamente para {empleado.nombre_completo} a las {datetime.now().strftime("%H:%M")}', 'success')
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
            flash(f'Salida registrada exitosamente para {empleado.nombre_completo} a las {hora_salida.strftime("%H:%M")}', 'success')
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
        visitante.fecha_salida = datetime.utcnow()
        visitante.estado_visita = 'Finalizada'
        visitante.activo = False
        db.session.commit()
        flash(f'Salida registrada para {visitante.nombre} {visitante.apellido} a las {visitante.fecha_salida.strftime("%H:%M")}', 'success')
    else:
        # Registrar entrada (nuevo visitante)
        visitante.fecha_entrada = datetime.utcnow()
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
    with app.app_context():
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
            print("Usuario administrador creado: admin@juancalito.com / nueva_contraseña_2024")
        
        print("Base de datos inicializada correctamente")
        print("Para agregar empleados de prueba, ejecuta: python agregar_empleados_prueba.py")

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
