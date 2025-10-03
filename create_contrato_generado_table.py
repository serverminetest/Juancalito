import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def create_contrato_generado_table():
    """Crea la tabla contrato_generado en la base de datos PostgreSQL."""
    print("🚀 Creando tabla contrato_generado...")
    
    # Obtener la URL de la base de datos
    database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL o DATABASE_PUBLIC_URL no configurada")
        return False
    
    print(f"📡 URL de conexión: {database_url[:50]}...")
    
    try:
        # Crear el motor de SQLAlchemy
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Verificar si la tabla ya existe
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'contrato_generado'
                );
            """))
            
            table_exists = result.scalar()
            
            if table_exists:
                print("✅ La tabla contrato_generado ya existe")
                return True
            
            # Crear la tabla contrato_generado
            connection.execute(text("""
                CREATE TABLE contrato_generado (
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
            print("✅ Tabla contrato_generado creada exitosamente")
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Error al crear la tabla: {e}")
        return False

if __name__ == '__main__':
    create_contrato_generado_table()
