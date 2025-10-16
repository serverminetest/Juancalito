# Flores Juncalito SAS - Sistema de Gestión

Sistema completo de gestión de empleados, contratos, asistencia y visitantes para Flores Juncalito SAS.

## 🚀 Características

- **Gestión de Empleados**: Registro completo con información personal, laboral y de contacto
- **Sistema de Asistencia**: QR diario para empleados + registro manual para administradores
- **Control de Visitantes**: QR diario para visitantes + registro manual
- **Gestión de Contratos**: Seguimiento de contratos y fechas de vencimiento
- **Reportes**: Generación de reportes de asistencia y empleados
- **Dashboard**: Panel de control con estadísticas en tiempo real

## 🛠️ Tecnologías

- **Backend**: Python Flask
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend**: Bootstrap 5 + HTML/CSS/JavaScript
- **Autenticación**: Flask-Login
- **QR Codes**: qrcode + Pillow

## 📋 Instalación Local

1. **Clonar el repositorio**:
```bash
git clone https://github.com/serverminetest/FloresJuncalito.git
cd FloresJuncalito
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Ejecutar la aplicación**:
```bash
python app.py
```

4. **Acceder a la aplicación**:
- URL: http://localhost:5000
- Usuario: `admin@floresjuncalito.com`
- Contraseña: `nueva_contraseña_2024`

## 🌐 Despliegue en Producción

### Railway (Recomendado)
1. Conecta tu repositorio de GitHub a Railway
2. Railway detectará automáticamente el `Procfile`
3. Agregará automáticamente PostgreSQL
4. La aplicación se desplegará automáticamente

### Render
1. Conecta tu repositorio de GitHub a Render
2. Selecciona "Web Service"
3. Render detectará automáticamente la configuración
4. Agregará PostgreSQL automáticamente

### Variables de Entorno
- `SECRET_KEY`: Clave secreta para Flask (generar una nueva para producción)
- `DATABASE_URL`: URL de PostgreSQL (se configura automáticamente en Railway/Render)

## 📱 Uso del Sistema

### Para Empleados
- Escanear QR diario para marcar entrada/salida
- Solo se permite una asistencia por día

### Para Visitantes
- Escanear QR diario para registrarse
- Completar formulario con datos personales y de emergencia

### Para Administradores
- Acceso completo al sistema
- Gestión de empleados, contratos y reportes
- Registro manual de asistencia y visitantes
- Visualización de estadísticas en tiempo real

## 🔧 Configuración

### Cambiar Credenciales de Administrador
Edita el archivo `app.py` en la función `init_db()`:
```python
admin_user = User(
    email='tu_email@empresa.com',
    username='Tu Nombre',
    password_hash=generate_password_hash('tu_nueva_contraseña'),
    is_admin=True
)
```

### Personalizar Colores
Edita el archivo `templates/base.html` para cambiar la paleta de colores.

## 📄 Licencia

Este proyecto es privado para Flores Juncalito SAS.