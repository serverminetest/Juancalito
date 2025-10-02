#!/usr/bin/env python3

from app import app, db, Empleado, Visitante, Asistencia, Contrato
from datetime import datetime, date, timedelta

def verificar_y_agregar():
    with app.app_context():
        print("Verificando datos existentes...")
        print(f"Empleados: {Empleado.query.count()}")
        print(f"Visitantes: {Visitante.query.count()}")
        print(f"Asistencias: {Asistencia.query.count()}")
        print(f"Contratos: {Contrato.query.count()}")
        
        # Si ya hay suficientes datos, no agregar más
        if Empleado.query.count() >= 4:
            print("✅ Ya hay suficientes datos en la base de datos")
            return
        
        print("\nAgregando datos adicionales...")
        
        # Agregar empleados con cédulas únicas
        empleados_nuevos = [
            Empleado(
                nombre_completo='Luis Fernando García',
                cedula='11223344',
                fecha_nacimiento=date(1988, 12, 3),
                genero='Masculino',
                estado_civil='Casado',
                telefono_principal='3003456789',
                email_personal='luis.garcia@email.com',
                direccion_residencia='Avenida 68 #12-34',
                ciudad='Cali',
                departamento='Valle del Cauca',
                cargo_puesto='Operario de Poscosecha',
                departamento_laboral='Poscosecha',
                fecha_ingreso=date(2022, 6, 1),
                tipo_contrato='Temporal',
                salario_base=2800000,
                tipo_salario='Mensual',
                jornada_laboral='Tiempo completo',
                ubicacion_trabajo='Planta',
                estado_empleado='Activo',
                eps='Nueva EPS',
                arl='Seguros Bolívar',
                afp='Colfondos',
                nombre_contacto_emergencia='Sandra García',
                telefono_emergencia='3007654321',
                parentesco='Esposa'
            ),
            Empleado(
                nombre_completo='María Elena Torres',
                cedula='55667788',
                fecha_nacimiento=date(1992, 4, 18),
                genero='Femenino',
                estado_civil='Soltera',
                telefono_principal='3004567890',
                email_personal='maria.torres@email.com',
                direccion_residencia='Calle 80 #45-12',
                ciudad='Bogotá',
                departamento='Cundinamarca',
                cargo_puesto='Asistente Administrativa',
                departamento_laboral='Administrativo',
                fecha_ingreso=date(2023, 2, 15),
                tipo_contrato='Indefinido',
                salario_base=3200000,
                tipo_salario='Mensual',
                jornada_laboral='Tiempo completo',
                ubicacion_trabajo='Oficina',
                estado_empleado='Activo',
                eps='Sanitas',
                arl='Positiva',
                afp='Protección',
                nombre_contacto_emergencia='Carlos Torres',
                telefono_emergencia='3006543210',
                parentesco='Padre'
            )
        ]
        
        for emp in empleados_nuevos:
            # Verificar si ya existe
            if not Empleado.query.filter_by(cedula=emp.cedula).first():
                db.session.add(emp)
                print(f"✅ Agregado empleado: {emp.nombre_completo}")
            else:
                print(f"⚠️  Empleado ya existe: {emp.nombre_completo}")
        
        db.session.commit()
        
        # Agregar visitantes adicionales
        visitantes_nuevos = [
            Visitante(
                nombre='Pedro',
                apellido='Mendoza',
                documento='33445566',
                eps='Sanitas',
                rh='O+',
                telefono='3006789012',
                empresa='Cliente ABC',
                motivo_visita='Reunión comercial',
                empleado_visitado='Juan Carlos Pérez',
                fecha_entrada=datetime.now() - timedelta(hours=1),
                estado_visita='En visita',
                nombre_contacto_emergencia='Laura Mendoza',
                telefono_emergencia='3004321098',
                parentesco='Esposa',
                activo=True
            ),
            Visitante(
                nombre='Sandra',
                apellido='López',
                documento='77889900',
                eps='Sura',
                rh='A+',
                telefono='3007890123',
                empresa='Proveedor XYZ',
                motivo_visita='Entrega de productos',
                empleado_visitado='Ana María Rodríguez',
                fecha_entrada=datetime.now() - timedelta(hours=2),
                fecha_salida=datetime.now() - timedelta(hours=1),
                estado_visita='Finalizada',
                nombre_contacto_emergencia='Miguel López',
                telefono_emergencia='3003210987',
                parentesco='Esposo',
                activo=True
            )
        ]
        
        for vis in visitantes_nuevos:
            if not Visitante.query.filter_by(documento=vis.documento).first():
                db.session.add(vis)
                print(f"✅ Agregado visitante: {vis.nombre} {vis.apellido}")
            else:
                print(f"⚠️  Visitante ya existe: {vis.nombre} {vis.apellido}")
        
        db.session.commit()
        
        # Agregar asistencias para empleados que no tienen
        empleados = Empleado.query.all()
        fecha_hoy = date.today()
        
        for empleado in empleados:
            if not Asistencia.query.filter_by(empleado_id=empleado.id, fecha=fecha_hoy).first():
                asistencia = Asistencia(
                    empleado_id=empleado.id,
                    fecha=fecha_hoy,
                    hora_entrada=datetime.now().time(),
                    token_diario='qr'
                )
                db.session.add(asistencia)
                print(f"✅ Agregada asistencia para: {empleado.nombre_completo}")
        
        db.session.commit()
        
        # Agregar contratos para empleados que no tienen
        for empleado in empleados:
            if not Contrato.query.filter_by(empleado_id=empleado.id, activo=True).first():
                contrato = Contrato(
                    empleado_id=empleado.id,
                    tipo_contrato=empleado.tipo_contrato,
                    fecha_inicio=empleado.fecha_ingreso,
                    fecha_fin=date(2025, 12, 31) if empleado.tipo_contrato == 'Indefinido' else date(2024, 12, 31),
                    salario=empleado.salario_base,
                    descripcion=f'Contrato {empleado.tipo_contrato.lower()} para {empleado.cargo_puesto}',
                    activo=True
                )
                db.session.add(contrato)
                print(f"✅ Agregado contrato para: {empleado.nombre_completo}")
        
        db.session.commit()
        
        print(f"\n📊 Resumen final:")
        print(f"- Empleados: {Empleado.query.count()}")
        print(f"- Visitantes: {Visitante.query.count()}")
        print(f"- Asistencias hoy: {Asistencia.query.filter_by(fecha=fecha_hoy).count()}")
        print(f"- Contratos: {Contrato.query.count()}")

if __name__ == '__main__':
    verificar_y_agregar()
