import datetime
import json as pyjson
from flask_mail import Mail, Message
import pandas as pd
from flask import Blueprint, current_app, json, jsonify, render_template, request, redirect, session, url_for, send_from_directory, flash, send_file 
from flask_login import current_user, login_user, logout_user, login_required
import qrcode
from werkzeug.utils import secure_filename
from app import db
from io import BytesIO 
import os
import requests # Necesario para verificar reCAPTCHA v3
import logging
from app.models import Aviso, ContactoEmergencia,  Evento, File, Folder, FormularioRespuesta, PortalWeb, Respuesta, User, VacationRequest, Noticia, RegistroCompetencia, EvaluacionDesempeno, AsistenciaFinAnio
from app.forms import LoginForm
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from app import mail
import smtplib
import openpyxl
USUARIOS_RESTRINGIDOS_P5 = {

}
def filtrar_portales_para_usuario(user_id):
    portales = PortalWeb.query.all()
    portales_filtrados = []
    for portal in portales:
        if portal.id == 5 and user_id in USUARIOS_RESTRINGIDOS_P5:
            continue
        portales_filtrados.append(portal)
    return portales_filtrados
main = Blueprint('main', __name__)

@main.route('/consultar_evaluaciones')
@login_required
def consultar_evaluaciones():
    allowed_ids = [304]  
    if current_user.id not in allowed_ids:
        return """
        <script>
            alert("No tienes los permisos necesarios para ver esta información.");
            window.location.href = "/";
        </script>
        """
    preguntas = [
    "Conozco mis funciones y mis responsabilidades",
    "Al realizar mi trabajo, siempre doy resultados positivos",
    "Las actividades que realizo me permiten desarrollar mis habilidades",
    "Tengo conocimiento de las políticas y reglamentos de la institución",
    "Puedo agilizar el trabajo actuando antes de que me lo pidan",
    "Ofrezco ayuda sin necesidad de que lo soliciten",
    "Me mantiene informado sobre asuntos que afectan a mi trabajo",
    "Pone el ejemplo en la forma en la que debe ser nuestro desempeño",
    "Soluciona los problemas de manera eficaz",
    "Encomienda las actividades de trabajo de manera igualitaria entre los compañeros",
    "Trata de igual manera a todo el personal y se comunica con respeto",
    "Identifica áreas de mejora optimizando el desempeño de nuestras funciones",
    "Siempre hay colaboración con mis compañeros para el buen desempeño del trabajo",
    "Me siento parte de un equipo de trabajo",
    "Es fácil expresar las opiniones ante compañeros y jefe inmediato",
    "Se generan planes de trabajo positivos que motivan al personal",
    "Se tiene un ambiente sano y cordial entre los compañeros de las otras estaciones",
    "Existe colaboración entre los compañeros de toda la institución para la realización de las tareas",
    "El nombre y prestigio de la institución me hacen sentir orgulloso de pertenecer a ella",
    "Conozco el trabajo que realizan las diferentes áreas de la institución",
    "Las estaciones cuentan con una instalación que permite sentirme a gusto",
    "Recibo capacitaciones constantes que permiten actualizar mis conocimientos sobre el trabajo",
    "Doy un buen uso y cuidado a las herramientas y equipo otorgado por la institución",
    "Me gusta la estación a la que pertenezco",
    "Descubro los intereses de mis compañeros e intento llevarlos a una meta en común",
    "Intento ser honesto y transparente cuando hablo",
    "Me considero una persona que explica con detalle cuando capacito a mis compañeros",
    "Conozco a mis compañeros y tengo muy buena relación con ellos",
    "Intento ofrecer todo mi apoyo cuando un compañero pasa por un momento de dificultad personal",
    "Escucho, respeto y reflexiono sobre las opiniones de los demás antes de tomar decisiones",
    "Me gusta dirigir las reuniones de trabajo para que todos participen",
    "Supervisar de cerca el equipo es buena opción para asegurarme que las cosas salgan bien",
    "Me cuesta trabajo admitir mis errores y suelo culpar a los demás",
    "Es bueno que nos asignen tareas sin decidir si está bien o no",
    "No acepto mis fracasos personales ni la opinión de que estoy equivocado en mi forma de ver las cosas",
    "Exijo superar las metas que consigue mi equipo con el fin de seguir mejorando",
    "Tengo una comunicación abierta con mis compañeros/personal a cargo y conozco lo que esperan de mí",
    "Los errores y fracasos de los demás los utilizo como motivación para superarlos",
    "Me gusta pensar de manera positiva para motivar al personal que me rodea y cumplir con los objetivos que se esperan en el trabajo",
    "Me da miedo tomar el control y prefiero que otros se encarguen",
    "Busco opiniones de mis compañeros para lograr ideas y proyectos nuevos",
    "Conseguir resultados positivos es mi prioridad, la tensión es el precio a pagar por el éxito",
    "Cuando hay problemas en mi equipo, me pongo muy nervioso y no sé cómo controlarme",
    "Soy una persona protectora con los compañeros que piensan igual que yo y obedecen, respeto a los que me contradices pero me cuesta mucho confiar en los que mienten"
]

    respuesta_texto = {
        "1": "Totalmente en desacuerdo",
        "2": "En desacuerdo",
        "3": "Indiferente",
        "4": "De acuerdo",
        "5": "Totalmente de acuerdo"
    }

    orden = request.args.get("orden", "desc")  
    seleccionado_id = request.args.get("id")  

    if seleccionado_id:  
        evaluaciones = EvaluacionDesempeno.query.filter_by(id=seleccionado_id).all()
    else:
        evaluaciones = EvaluacionDesempeno.query.all()

    evaluaciones_data = []
    for evaluacion in evaluaciones:
        respuestas = evaluacion.respuestas
        total = 0
        count = 0
        promedios_rubro = {
            "Desempeño": 0,
            "Jefe Inmediato": 0,
            "Apoyo y Convivencia": 0,
            "Pertenencia": 0,
            "Clasificación": 0
        }
        for rubro, preguntas in respuestas.items():
            valores = [int(v) for v in preguntas.values() if v]
            if valores:
                promedio_rubro = round(sum(valores) / len(valores), 2)
            else:
                promedio_rubro = 0

            if rubro == "desempeno":
                promedios_rubro["Desempeño"] = promedio_rubro
            elif rubro == "jefe_inmediato":
                promedios_rubro["Jefe Inmediato"] = promedio_rubro
            elif rubro == "apoyo_convivencia":
                promedios_rubro["Apoyo y Convivencia"] = promedio_rubro
            elif rubro == "pertenencia":
                promedios_rubro["Pertenencia"] = promedio_rubro
            elif rubro == "clasificacion":
                promedios_rubro["Clasificación"] = promedio_rubro

            total += sum(valores)
            count += len(valores)

        promedio = round(total / count, 2) if count > 0 else 0

        evaluaciones_data.append({
            "id": evaluacion.id,
            "nombre": evaluacion.nombre,
            "respuestas": respuestas,
            "promedio": promedio,
            "promedios_rubro": promedios_rubro
        })

    # ordenar lista
    reverse = (orden == "desc")
    evaluaciones_data.sort(key=lambda x: x["promedio"], reverse=reverse)

    # Calcular promedios generales
    promedios = {
        "Desempeño": [],
        "Jefe Inmediato": [],
        "Apoyo y Convivencia": [],
        "Pertenencia": [],
        "Clasificación": []
    }
    conteo = {k: 0 for k in promedios}

    for e in evaluaciones:
        for rubro, preguntas in e.respuestas.items():
            valores = [int(v) for v in preguntas.values() if v]
            if valores:
                promedio_rubro = round(sum(valores) / len(valores), 2)
                if rubro == "desempeno":
                    promedios["Desempeño"].append(promedio_rubro)
                    conteo["Desempeño"] += 1
                elif rubro == "jefe_inmediato":
                    promedios["Jefe Inmediato"].append(promedio_rubro)
                    conteo["Jefe Inmediato"] += 1
                elif rubro == "apoyo_convivencia":
                    promedios["Apoyo y Convivencia"].append(promedio_rubro)
                    conteo["Apoyo y Convivencia"] += 1
                elif rubro == "pertenencia":
                    promedios["Pertenencia"].append(promedio_rubro)
                    conteo["Pertenencia"] += 1
                elif rubro == "clasificacion":
                    promedios["Clasificación"].append(promedio_rubro)
                    conteo["Clasificación"] += 1

    # promedio final por rubro
    promedios_finales = []
    for rubro, valores in promedios.items():
        if valores:
            promedios_finales.append(round(sum(valores) / len(valores), 2))
        else:
            promedios_finales.append(0)

    return render_template(
        'consultar_evaluaciones.html',
        evaluaciones=evaluaciones_data,
        promedios=promedios_finales,
        respuesta_texto=respuesta_texto,
        orden=orden,
        seleccionado_id=seleccionado_id  
    )

@main.route('/descargar_asistencia_excel_formato')
@login_required
def descargar_asistencia_excel_formato():
    asistentes_data = db.session.query(
        AsistenciaFinAnio.nombre_usuario,
        User.username,
        User.turno,  
        AsistenciaFinAnio.lleva_acompanante,
        AsistenciaFinAnio.fecha_registro
    ).join(User, AsistenciaFinAnio.user_id == User.id) \
     .filter(AsistenciaFinAnio.asistencia == 'sí') \
     .order_by(AsistenciaFinAnio.nombre_usuario) \
     .all()
    data = []
    for nombre_usuario, username, turno, lleva_acompanante, fecha_registro in asistentes_data:
        lleva_acompanante_str = "Sí" if lleva_acompanante == 'sí' else "No"
        data.append({
            'Nombre del Empleado': nombre_usuario,
            'Username': username,
            'Turno': turno if turno else 'N/A', 
            'Asistencia': 'Sí',
            'Lleva Acompañante': lleva_acompanante_str,
            'Fecha de Registro': fecha_registro.strftime('%Y-%m-%d %H:%M:%S')
        })
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Asistentes', index=False)
        worksheet = writer.sheets['Asistentes']
        header_font = openpyxl.styles.Font(bold=True)
        side_border = openpyxl.styles.Side(style='thin')
        full_border = openpyxl.styles.Border(left=side_border, 
                                             right=side_border, 
                                             top=side_border, 
                                             bottom=side_border)
        for col_num, value in enumerate(df.columns, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = value
            cell.font = header_font
            cell.border = full_border
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter 
            for cell in col:
                try:
                    cell.border = full_border
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column].width = adjusted_width
    output.seek(0)
    filename = "Lista_Asistencia_Fin_Anio.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )        


@main.route('/registro_fin_anio12w', methods=['GET', 'POST'])
@login_required
def submit_fin():
    if request.method == 'POST':
        asistencia = request.form.get('asistencia')
        lleva_acompanante = request.form.get('lleva_acompanante')
        user_id = current_user.id
        nombre_del_usuario = current_user.nombre 
        
        if not asistencia or not lleva_acompanante:
            flash('Por favor, responde a todas las preguntas de asistencia.', 'danger')
            return redirect(url_for('main.submit_fin'))
            
        registro_existente = AsistenciaFinAnio.query.filter_by(user_id=user_id).first()
        
        try:
            if registro_existente:
                registro_existente.asistencia = asistencia
                registro_existente.lleva_acompanante = lleva_acompanante
                registro_existente.nombre_usuario = nombre_del_usuario 
                flash('✅ Tu registro de asistencia ha sido **actualizado** exitosamente.', 'success')
            else:
                nuevo_registro = AsistenciaFinAnio(
                    user_id=user_id,
                    nombre_usuario=nombre_del_usuario, 
                    asistencia=asistencia,
                    lleva_acompanante=lleva_acompanante
                )
                db.session.add(nuevo_registro)
                flash('💾 Tu registro ha sido **guardado** exitosamente. ¡Gracias!', 'success')
            db.session.commit()
            if asistencia == 'sí': 

                return redirect(url_for('main.confirmacion_exitosa'))

            else:
                return redirect(url_for('main.cancelacion'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Ocurrió un error al guardar tu respuesta: {e}', 'danger')
            return redirect(url_for('main.submit_fin'))
    registro = AsistenciaFinAnio.query.filter_by(user_id=current_user.id).first()
    return render_template('confirmation.html', registro=registro)



@main.route('/dashboard')
@login_required
def dashboard():
    uploads_path = current_app.config['UPLOAD_FOLDER']
    static_uploads_path = os.path.join(current_app.root_path, 'static', 'uploads')
    username = current_user.username
    user_image_path = os.path.join(static_uploads_path, f"{username}.jpg")

    if os.path.exists(user_image_path):
        user_image = f"uploads/{username}.jpg"
    else:
        user_image = "uploads/default.png"
    files_in_db = File.query.all()
    visible_files = []
    for file in files_in_db:
        filepath = os.path.join(uploads_path, file.filename)
        if os.path.exists(filepath):
            visible_files.append(file)
    avisos = Aviso.query.order_by(Aviso.fecha_creacion.desc()).all()
    eventos = Evento.query.order_by(Evento.fecha.asc()).all()
    noticias = Noticia.query.order_by(Noticia.orden.asc()).all()
    portales = filtrar_portales_para_usuario(current_user.id)

    return render_template(
        'dashboard.html',
        files=visible_files,  
        avisos=avisos,
        eventos=eventos,
        noticias=noticias,
        portales=portales,
        user_image=user_image
    )
@main.route('/uploads/<filename>')
@login_required
def serve_uploaded_file(filename):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)


@main.route('/sw.js')
def service_worker():
    response = send_from_directory(os.path.join(current_app.root_path, 'static', 'js'), 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response
@main.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.username == 'admin':
                if not form.password.data or not user.check_password(form.password.data):
                    flash('Contraseña incorrecta.', 'danger')
                    return render_template('login.html', form=form)
            login_user(user)
            flash('Inicio de sesión exitoso.', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Usuario incorrecto.', 'danger')

    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('main.login'))

@main.route('/submit_evaluacion', methods=['POST'])
@login_required
def submit_evaluacion():
    try:
        # Obtener el ID del usuario que será evaluado
        evaluado_id = request.form.get('evaluado_id')
        
        if not evaluado_id:
            flash("Usuario no seleccionado", "danger")
            return redirect(request.referrer)
        
        evaluado_id = int(evaluado_id)
        
        # Validar permisos para evaluación personal
        PERMISOS_EVALUACION = {
            7: [30, 42, 49],
            263: [101, 111, 182],
            63: [148, 180, 185, 264, 301, 303]
        }
        
        evaluador_id = current_user.id
        usuarios_permitidos = PERMISOS_EVALUACION.get(evaluador_id, [])
        
        # Si el evaluador tiene permisos restringidos y el evaluado no está en su lista
        if evaluador_id in PERMISOS_EVALUACION and evaluado_id not in usuarios_permitidos:
            flash("No tienes permiso para evaluar a este usuario", "danger")
            return redirect(request.referrer)
        
        # Verificar si ya existe una evaluación del mismo evaluador al mismo evaluado
        evaluacion_existente = EvaluacionDesempeno.query.filter_by(
            user_id=evaluado_id,
            evaluador_id=current_user.id
        ).first()
        
        if evaluacion_existente:
            flash("Ya has evaluado a esta persona. No puedes hacer una evaluación duplicada.", "warning")
            return redirect(request.referrer)
        
        # Recibimos los datos del formulario
        nombre = request.form.get('nombre')
        fecha_str = request.form.get('fecha')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        area = request.form.get('area') or ""  # área es opcional
        estacion = request.form.get('estacion') or ""  # estación es opcional
        nomina = request.form.get('nomina')
        puesto = request.form.get('puesto')
        
        # Almacenamos las respuestas del formulario en un diccionario
        # Estructura genérica que soporta evaluaciones (subteniente, teniente y coordinador)
        respuestas = {
            # Para evaluación de Subteniente
            'comunicacion': {
                'claridad': request.form.get('comunicacion_claridad') or None,
                'escucha': request.form.get('comunicacion_escucha') or None,
                'equipo': request.form.get('comunicacion_equipo') or None,
                'conflictos': request.form.get('comunicacion_conflictos') or None
            },
            # Para evaluación de Teniente - Conocimientos Bomberiles
            'conocimientos': {
                'dominio_tecnico': request.form.get('conocimientos_dominio_tecnico') or None,
                'uso_equipo': request.form.get('conocimientos_uso_equipo') or None,
                'normatividad': request.form.get('conocimientos_normatividad') or None,
                'toma_decisiones': request.form.get('conocimientos_toma_decisiones') or None
            },
            # Para evaluación de Coordinador - Dirección de Guardias
            'direccion': {
                'direccion_guardias': request.form.get('direccion_guardias') or None,
                'toma_decisiones': request.form.get('direccion_toma_decisiones') or None,
                'motivacion': request.form.get('direccion_motivacion') or None,
                'normatividad': request.form.get('direccion_normatividad') or None
            },
            # Para evaluación de Coordinador - Gestión de Estaciones
            'gestion': {
                'organizacion': request.form.get('gestion_organizacion') or None,
                'protocolos': request.form.get('gestion_protocolos') or None,
                'supervisiona_mantenimiento': request.form.get('gestion_supervisiona_mantenimiento') or None,
                'adaptabilidad': request.form.get('gestion_adaptabilidad') or None
            },
            # Habilidades Blandas
            'habilidades_blandas': {
                'trabajo_equipo': request.form.get('blandas_trabajo_equipo') or None,
                'empatia': request.form.get('blandas_empatia') or None,
                'adaptabilidad': request.form.get('blandas_adaptabilidad') or None,
                'responsabilidad': request.form.get('blandas_responsabilidad') or None,
                'liderazgo': request.form.get('blandas_liderazgo') or None,
                'resolucion_conflictos': request.form.get('blandas_resolucion_conflictos') or None
            },
            # Comunicación con Subordinados (para Teniente y Coordinador)
            'comunicacion_subordinados': {
                'claridad_instrucciones': request.form.get('comunicacion_claridad_instrucciones') or None,
                'retroalimentacion': request.form.get('comunicacion_retroalimentacion') or None,
                'escucha_activa': request.form.get('comunicacion_escucha_activa') or None,
                'situaciones_criticas': request.form.get('comunicacion_situaciones_criticas') or None
            },
            # Disciplina
            'disciplina': {
                'puntualidad': request.form.get('disciplina_puntualidad') or None,
                'normas': request.form.get('disciplina_normas') or None,
                'presentacion': request.form.get('disciplina_presentacion') or None,
                'recursos': request.form.get('disciplina_recursos') or None,
                'imparcialidad': request.form.get('disciplina_imparcialidad') or None,
                'prevencion': request.form.get('disciplina_prevencion') or None,
                'documentacion': request.form.get('disciplina_documentacion') or None,
                'autoridad_moral': request.form.get('disciplina_autoridad_moral') or None
            },
            # Orden Cerrado
            'orden_cerrado': {
                'dominio': request.form.get('orden_cerrado_dominio') or None,
                'coordinacion': request.form.get('orden_cerrado_coordinacion') or None,
                'atencion': request.form.get('orden_cerrado_atencion') or None,
                'postura': request.form.get('orden_cerrado_postura') or None,
                'dominio_tecnicas': request.form.get('orden_cerrado_dominio_tecnicas') or None,
                'coordinacion_grupal': request.form.get('orden_cerrado_coordinacion_grupal') or None,
                'correccion_errores': request.form.get('orden_cerrado_correccion_errores') or None,
                'presencia_porte': request.form.get('orden_cerrado_presencia_porte') or None
            }
        }

        observaciones = request.form.get('observaciones')

        # Crear un objeto de la evaluación
        evaluacion = EvaluacionDesempeno(
            user_id=evaluado_id,
            evaluador_id=current_user.id,
            nombre=nombre,
            fecha=fecha,
            area=area,
            estacion=estacion,
            nomina=nomina,
            puesto=puesto,
            respuestas=respuestas,
            evaluacion_general=observaciones,
            comentario=observaciones
        )

        # Guardar la evaluación en la base de datos
        db.session.add(evaluacion)
        db.session.commit()

        flash("Evaluación enviada exitosamente", "success")  # Mostrar un mensaje de éxito

        # Redirigir al dashboard
        return redirect(url_for('main.dashboard'))
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error en submit_evaluacion: {str(e)}")
        flash(f"Error al guardar la evaluación: {str(e)}", "danger")
        return redirect(request.referrer)

@main.route('/resultados_evaluaciones')
@login_required
def resultados_evaluaciones():
    try:
        rol_seleccionado = request.args.get('rol', 'BOMBERO ESPECIALIZADO').strip()
        turno_seleccionado = request.args.get('turno', 'GENERAL').strip()
        
        logging.info(f"[DEBUG] Parámetros recibidos: rol='{rol_seleccionado}', turno='{turno_seleccionado}'")
        
        # Obtener todos los usuarios del rol seleccionado
        if turno_seleccionado == 'GENERAL':
            # Si es GENERAL, obtener todos los usuarios del rol sin filtrar por turno
            logging.info(f"[DEBUG] Filtrando GENERAL - obteniendo todos los usuarios con puesto='{rol_seleccionado}'")
            usuarios = User.query.filter_by(puesto=rol_seleccionado).all()
        else:
            # Si es un turno específico, filtrar por puesto y turno
            logging.info(f"[DEBUG] Filtrando turno específico - puesto='{rol_seleccionado}', turno='{turno_seleccionado}'")
            usuarios = User.query.filter_by(puesto=rol_seleccionado, turno=turno_seleccionado).all()
        
        usuario_ids = [u.id for u in usuarios]
        logging.info(f"[DEBUG] Usuarios encontrados: {len(usuarios)} con IDs: {usuario_ids[:10]}...")  # Mostrar primeros 10
        
        # Obtener todas las evaluaciones de estos usuarios
        if usuario_ids:
            evaluaciones = EvaluacionDesempeno.query.filter(
                EvaluacionDesempeno.user_id.in_(usuario_ids)
            ).all()
        else:
            evaluaciones = []
        
        # Definir categorías por rol evaluado
        categorias_por_rol = {
            'BOMBERO ESPECIALIZADO': {
                'comunicacion': {'titulo': 'Comunicación', 'valores': []},
                'habilidades_blandas': {'titulo': 'Habilidades Blandas', 'valores': []},
                'disciplina': {'titulo': 'Disciplina', 'valores': []},
                'orden_cerrado': {'titulo': 'Orden Cerrado', 'valores': []}
            },
            'SUBTENIENTE': {
                'conocimientos': {'titulo': 'Conocimientos Bomberiles', 'valores': []},
                'habilidades_blandas': {'titulo': 'Habilidades Blandas', 'valores': []},
                'comunicacion_subordinados': {'titulo': 'Comunicación con Subordinados', 'valores': []},
                'disciplina': {'titulo': 'Disciplina', 'valores': []},
                'orden_cerrado': {'titulo': 'Orden Cerrado', 'valores': []}
            },
            'TENIENTE': {
                'direccion': {'titulo': 'Dirección de Guardias y Turnos', 'valores': []},
                'gestion': {'titulo': 'Gestión de Estaciones', 'valores': []},
                'comunicacion_subordinados': {'titulo': 'Comunicación con Subordinados', 'valores': []},
                'disciplina': {'titulo': 'Disciplina', 'valores': []},
                'orden_cerrado': {'titulo': 'Orden Cerrado', 'valores': []}
            }
        }
        
        # Obtener categorías para el rol seleccionado
        categorias = categorias_por_rol.get(rol_seleccionado, categorias_por_rol['BOMBERO ESPECIALIZADO'])
        
        logging.info(f"Consultando evaluaciones para rol: {rol_seleccionado}, turno: {turno_seleccionado}")
        logging.info(f"Total de evaluaciones encontradas: {len(evaluaciones)}")
        
        for evaluacion in evaluaciones:
            if not evaluacion or not evaluacion.respuestas:
                continue
            
            respuestas = evaluacion.respuestas
            
            # Si respuestas es string (JSON encoded), deserializarlo
            if isinstance(respuestas, str):
                try:
                    respuestas = pyjson.loads(respuestas)
                except pyjson.JSONDecodeError:
                    logging.error(f"Error deserializando JSON en evaluación {evaluacion.id}")
                    continue
            
            if not isinstance(respuestas, dict):
                logging.warning(f"Respuestas no es dict: {type(respuestas)}")
                continue
            
            for categoria, datos in categorias.items():
                if categoria not in respuestas:
                    continue
                
                categoria_data = respuestas[categoria]
                if not isinstance(categoria_data, dict):
                    continue
                
                try:
                    # Convertir valores a int y filtrar los que no sean válidos
                    valores = []
                    for v in categoria_data.values():
                        if v:  # Skip None y empty strings
                            try:
                                valores.append(int(v))
                            except (ValueError, TypeError):
                                # Skip values that can't be converted to int
                                pass
                    
                    if valores:
                        promedio = sum(valores) / len(valores)
                        datos['valores'].append(promedio)
                except Exception as e:
                    logging.error(f"Error processing categoria {categoria}: {str(e)}")
                    continue
        
        # Calcular promedios finales y contar evaluaciones
        datos_grafica = []
        for categoria, datos in categorias.items():
            if datos['valores']:
                promedio_final = sum(datos['valores']) / len(datos['valores'])
            else:
                promedio_final = 0
            
            datos_grafica.append({
                'nombre': datos['titulo'],
                'promedio': round(promedio_final, 2),
                'cantidad_evaluaciones': len(datos['valores'])
            })
        
        return render_template(
            'resultados_evaluaciones.html',
            datos_grafica=datos_grafica,
            rol_seleccionado=rol_seleccionado,
            turno_seleccionado=turno_seleccionado,
            total_evaluaciones=len(evaluaciones),
            roles_disponibles=['BOMBERO ESPECIALIZADO', 'SUBTENIENTE', 'TENIENTE'],
            turnos_disponibles=['GENERAL', 'A', 'B', 'C']
        )
    except Exception as e:
        logging.error(f"Error en resultados_evaluaciones: {str(e)}")
        flash(f"Error al cargar los resultados: {str(e)}", "danger")
        return redirect(url_for('main.dashboard'))


@main.route('/descargar_resultados_excel', methods=['GET'])
@login_required
def descargar_resultados_excel():
    try:
        rol_seleccionado = request.args.get('rol', 'BOMBERO ESPECIALIZADO')
        turno_seleccionado = request.args.get('turno', 'GENERAL')
        
        # Obtener usuarios del rol seleccionado
        if turno_seleccionado == 'GENERAL':
            usuarios = User.query.filter_by(puesto=rol_seleccionado).all()
        else:
            usuarios = User.query.filter_by(puesto=rol_seleccionado, turno=turno_seleccionado).all()
        
        usuario_ids = [u.id for u in usuarios]
        
        # Obtener evaluaciones
        if usuario_ids:
            evaluaciones = EvaluacionDesempeno.query.filter(
                EvaluacionDesempeno.user_id.in_(usuario_ids)
            ).all()
        else:
            evaluaciones = []
        
        # Definir categorías por rol
        categorias_por_rol = {
            'BOMBERO ESPECIALIZADO': {
                'comunicacion': 'Comunicación',
                'habilidades_blandas': 'Habilidades Blandas',
                'disciplina': 'Disciplina',
                'orden_cerrado': 'Orden Cerrado'
            },
            'SUBTENIENTE': {
                'conocimientos': 'Conocimientos Bomberiles',
                'habilidades_blandas': 'Habilidades Blandas',
                'comunicacion_subordinados': 'Comunicación con Subordinados',
                'disciplina': 'Disciplina',
                'orden_cerrado': 'Orden Cerrado'
            },
            'TENIENTE': {
                'direccion': 'Dirección de Guardias y Turnos',
                'gestion': 'Gestión de Estaciones',
                'comunicacion_subordinados': 'Comunicación con Subordinados',
                'disciplina': 'Disciplina',
                'orden_cerrado': 'Orden Cerrado'
            }
        }
        
        categorias = categorias_por_rol.get(rol_seleccionado, categorias_por_rol['BOMBERO ESPECIALIZADO'])
        
        # Procesar datos de evaluaciones - DATOS AGREGADOS y DETALLADOS
        datos_categorias_agregados = {cat: [] for cat in categorias.keys()}
        datos_usuarios = {}  # {usuario_id: {categoria: [valores]}}
        
        for evaluacion in evaluaciones:
            if not evaluacion or not evaluacion.respuestas:
                continue
            
            usuario = User.query.get(evaluacion.user_id)
            evaluador = User.query.get(evaluacion.evaluador_id)
            if not usuario:
                continue
            
            respuestas = evaluacion.respuestas
            
            if isinstance(respuestas, str):
                try:
                    respuestas = pyjson.loads(respuestas)
                except:
                    continue
            
            if not isinstance(respuestas, dict):
                continue
            
            # Inicializar datos del usuario si no existen
            if evaluacion.user_id not in datos_usuarios:
                datos_usuarios[evaluacion.user_id] = {
                    'nombre': usuario.nombre,
                    'username': usuario.username,
                    'puesto': usuario.puesto,
                    'turno': usuario.turno or 'N/A',
                    'estacion': usuario.estacion or 'N/A',
                    'comentarios': [],
                    'categorias': {cat: [] for cat in categorias.keys()}
                }
            
            comentario_evaluacion = evaluacion.comentario.strip() if evaluacion.comentario else ''
            if comentario_evaluacion:
                datos_usuarios[evaluacion.user_id]['comentarios'].append(comentario_evaluacion)
            
            # Procesar cada categoría
            promedios_categorias = []
            for categoria in categorias.keys():
                if categoria not in respuestas:
                    continue
                
                categoria_data = respuestas[categoria]
                if not isinstance(categoria_data, dict):
                    continue
                
                valores = []
                for v in categoria_data.values():
                    if v:
                        try:
                            valores.append(int(v))
                        except (ValueError, TypeError):
                            pass
                
                if valores:
                    promedio = sum(valores) / len(valores)
                    promedios_categorias.append(promedio)
                    datos_categorias_agregados[categoria].append(promedio)
                    datos_usuarios[evaluacion.user_id]['categorias'][categoria].append(promedio)
            
            # Calcular calificación general como promedio de todos los promedios
            if promedios_categorias:
                calificacion_general = sum(promedios_categorias) / len(promedios_categorias)
                # No se utiliza al nivel usuario directo, pero sí permite conservar el cálculo si se necesita.
        
        # Crear Excel con dos hojas
        wb = openpyxl.Workbook()
        
        # Estilos
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        header_fill = PatternFill(start_color="2563eb", end_color="2563eb", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        user_header_fill = PatternFill(start_color="0891b2", end_color="0891b2", fill_type="solid")
        user_header_font = Font(bold=True, color="FFFFFF", size=11)
        excellent_fill = PatternFill(start_color="86efac", end_color="86efac", fill_type="solid")  # Verde
        good_fill = PatternFill(start_color="fbbf24", end_color="fbbf24", fill_type="solid")  # Amarillo
        poor_fill = PatternFill(start_color="f87171", end_color="f87171", fill_type="solid")  # Rojo
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # ===== HOJA 1: RESUMEN =====
        ws_resumen = wb.active
        ws_resumen.title = "Resumen"
        
        ws_resumen['A1'] = "RESULTADOS DE EVALUACIONES DEL DESEMPEÑO"
        ws_resumen['A1'].font = Font(bold=True, size=14, color="1e293b")
        ws_resumen.merge_cells('A1:C1')
        
        ws_resumen['A2'] = f"Puesto: {rol_seleccionado}"
        ws_resumen['B2'] = f"Turno: {turno_seleccionado}"
        ws_resumen['C2'] = f"Total de Evaluaciones: {len(evaluaciones)}"
        
        # Tabla de resumen
        row = 4
        ws_resumen[f'A{row}'] = "Categoría"
        ws_resumen[f'B{row}'] = "Promedio (de 5)"
        ws_resumen[f'C{row}'] = "Cantidad de Evaluaciones"
        
        for col in ['A', 'B', 'C']:
            ws_resumen[f'{col}{row}'].fill = header_fill
            ws_resumen[f'{col}{row}'].font = header_font
            ws_resumen[f'{col}{row}'].alignment = Alignment(horizontal='center', vertical='center')
            ws_resumen[f'{col}{row}'].border = thin_border
        
        row += 1
        for categoria, titulo in categorias.items():
            valores = datos_categorias_agregados[categoria]
            promedio = sum(valores) / len(valores) if valores else 0
            cantidad = len(valores)
            
            ws_resumen[f'A{row}'] = titulo
            ws_resumen[f'B{row}'] = round(promedio, 2)
            ws_resumen[f'C{row}'] = cantidad
            
            for col in ['A', 'B', 'C']:
                ws_resumen[f'{col}{row}'].border = thin_border
                ws_resumen[f'{col}{row}'].alignment = Alignment(horizontal='center', vertical='center')
            
            row += 1
        
        ws_resumen.column_dimensions['A'].width = 35
        ws_resumen.column_dimensions['B'].width = 20
        ws_resumen.column_dimensions['C'].width = 25
        
        # ===== HOJA 2: DETALLADO POR USUARIO =====
        ws_detallado = wb.create_sheet("Detallado por Usuario")
        
        # Encabezados
        ws_detallado['A1'] = "EVALUACIONES DETALLADAS POR USUARIO"
        ws_detallado['A1'].font = Font(bold=True, size=14, color="1e293b")
        
        row = 3
        ws_detallado[f'A{row}'] = "Nómina"
        ws_detallado[f'B{row}'] = "Nombre del Evaluado"
        ws_detallado[f'C{row}'] = "Puesto"
        ws_detallado[f'D{row}'] = "Turno"
        ws_detallado[f'E{row}'] = "Comentarios"
        
        # Agregar columnas para cada categoría
        col_idx = 6
        categoria_cols = {}
        for categoria, titulo in categorias.items():
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            ws_detallado[f'{col_letter}{row}'] = titulo
            categoria_cols[categoria] = col_letter
            col_idx += 1
        last_header_col = openpyxl.utils.get_column_letter(col_idx - 1)
        ws_detallado.merge_cells(f'A1:{last_header_col}1')
        
        # Estilos para encabezado
        for col in range(1, col_idx):
            col_letter = openpyxl.utils.get_column_letter(col)
            ws_detallado[f'{col_letter}{row}'].fill = user_header_fill
            ws_detallado[f'{col_letter}{row}'].font = user_header_font
            ws_detallado[f'{col_letter}{row}'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            ws_detallado[f'{col_letter}{row}'].border = thin_border
        
        # Llenar datos de usuarios
        row += 1
        for user_id in sorted(datos_usuarios.keys()):
            user_data = datos_usuarios[user_id]
            
            ws_detallado[f'A{row}'] = user_data['username']
            ws_detallado[f'B{row}'] = user_data['nombre']
            ws_detallado[f'C{row}'] = user_data['puesto']
            ws_detallado[f'D{row}'] = user_data['turno']
            comentarios_usuario = user_data['comentarios']
            ws_detallado[f'E{row}'] = '\n---\n'.join(comentarios_usuario) if comentarios_usuario else 'Sin comentarios'
            for col in ['A', 'B', 'C', 'D', 'E']:
                ws_detallado[f'{col}{row}'].border = thin_border
                ws_detallado[f'{col}{row}'].alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            
            # Llenar promedios por categoría
            for categoria, col_letter in categoria_cols.items():
                valores = user_data['categorias'][categoria]
                if valores:
                    promedio = sum(valores) / len(valores)
                    ws_detallado[f'{col_letter}{row}'] = round(promedio, 2)
                    
                    # Aplicar color según el promedio
                    if promedio >= 4.5:
                        fill_color = excellent_fill
                    elif promedio >= 3.5:
                        fill_color = good_fill
                    else:
                        fill_color = poor_fill
                    
                    ws_detallado[f'{col_letter}{row}'].fill = fill_color
                else:
                    ws_detallado[f'{col_letter}{row}'] = "N/A"
                
                ws_detallado[f'{col_letter}{row}'].border = thin_border
                ws_detallado[f'{col_letter}{row}'].alignment = Alignment(horizontal='center', vertical='center')
            
            row += 1
        
        ws_detallado.column_dimensions['A'].width = 18  
        ws_detallado.column_dimensions['B'].width = 30  
        ws_detallado.column_dimensions['C'].width = 20
        ws_detallado.column_dimensions['D'].width = 12
        ws_detallado.column_dimensions['E'].width = 40
        for categoria, col_letter in categoria_cols.items():
            ws_detallado.column_dimensions[col_letter].width = 18
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Evaluaciones_{rol_seleccionado.replace(' ', '_')}_{turno_seleccionado}_{fecha}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logging.error(f"Error al descargar resultados en Excel: {str(e)}")
        flash(f"Error al descargar los resultados: {str(e)}", "danger")
        return redirect(url_for('main.resultados_evaluaciones'))


@main.route('/api/evaluaciones_disponibles', methods=['GET'])
@login_required
def api_evaluaciones_disponibles():
    """API que retorna todas las evaluaciones disponibles para búsqueda"""
    try:
        evaluaciones = EvaluacionDesempeno.query.all()
        evaluaciones_list = []
        
        for eval in evaluaciones:
            usuario = User.query.get(eval.user_id)
            if usuario:
                evaluaciones_list.append({
                    'eval_id': eval.id,
                    'user_id': eval.user_id,
                    'nombre': usuario.nombre,
                    'nomina': usuario.username,
                    'puesto': usuario.puesto,
                    'turno': usuario.turno or 'N/A',
                    'estacion': usuario.estacion or 'N/A',
                    'fecha': eval.fecha.strftime('%d/%m/%Y') if eval.fecha else 'N/A'
                })
        
        return jsonify({'evaluaciones': evaluaciones_list})
    except Exception as e:
        logging.error(f"Error en API evaluaciones: {str(e)}")
        return jsonify({'error': str(e)}), 500


@main.route('/api/evaluacion/<int:eval_id>', methods=['GET'])
@login_required
def api_evaluacion_detalle(eval_id):
    """API que retorna los datos de una evaluación específica"""
    try:
        evaluacion = EvaluacionDesempeno.query.get(eval_id)
        if not evaluacion:
            return jsonify({'error': 'Evaluación no encontrada'}), 404
        
        usuario_evaluado = User.query.get(evaluacion.user_id)
        usuario_evaluador = User.query.get(evaluacion.evaluador_id)
        
        if not usuario_evaluado:
            return jsonify({'error': 'Usuario evaluado no encontrado'}), 404
        
        respuestas = evaluacion.respuestas
        temas_calificaciones = {}
        
        for tema, preguntas_dict in respuestas.items():
            valores = [int(v) for v in preguntas_dict.values() if v]
            if valores:
                promedio = round(sum(valores) / len(valores), 2)
                tema_nombres = {
                    'comunicacion': 'Comunicación',
                    'habilidades_blandas': 'Habilidades Blandas',
                    'disciplina': 'Disciplina',
                    'orden_cerrado': 'Orden Cerrado',
                    'conocimientos': 'Conocimientos Bomberiles',
                    'comunicacion_subordinados': 'Comunicación con Subordinados',
                    'liderazgo': 'Liderazgo'
                }
                tema_nombre = tema_nombres.get(tema, tema)
                temas_calificaciones[tema_nombre] = promedio
        
        return jsonify({
            'evaluacion': {
                'id': evaluacion.id,
                'fecha': evaluacion.fecha.strftime('%d/%m/%Y') if evaluacion.fecha else 'N/A',
                'comentario': evaluacion.comentario or '',
            },
            'usuario_evaluado': {
                'nombre': usuario_evaluado.nombre,
                'puesto': usuario_evaluado.puesto,
                'turno': usuario_evaluado.turno or 'N/A',
                'estacion': usuario_evaluado.estacion or 'N/A',
                'username': usuario_evaluado.username
            },
            'usuario_evaluador': {
                'nombre': usuario_evaluador.nombre if usuario_evaluador else 'N/A',
            },
            'temas_calificaciones': temas_calificaciones
        })
    except Exception as e:
        logging.error(f"Error en API evaluacion detalle: {str(e)}")
        return jsonify({'error': str(e)}), 500


@main.route('/submit_form', methods=['POST'])
@login_required
def submit_form():
    nombre = request.form.get('nombre')
    email = request.form.get('email')
    mensaje = request.form.get('mensaje')
    flash(f'Mensaje recibido de {nombre}', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@main.before_request
def verificar_inactividad():
    session.permanent = True  
    session.modified = True  

    if 'ultima_actividad' in session:
        ultima_actividad_str = session.get('ultima_actividad')

        if isinstance(ultima_actividad_str, str): 
            try:
                ultima_actividad = datetime.fromisoformat(ultima_actividad_str)  
            except ValueError:
                ultima_actividad = datetime.now()  
        else:
            ultima_actividad = datetime.now()  
        
        tiempo_inactivo = datetime.now() - ultima_actividad
        if tiempo_inactivo > timedelta(hours=2):
            logout_user()
            session.clear()
            flash('Tu sesión ha expirado por inactividad.', 'warning')
            return redirect(url_for('main.login'))
    session['ultima_actividad'] = datetime.now().isoformat()  

@main.route('/check_vacation_status', methods=['GET'])
@login_required
def check_vacation_status():
    vacation = VacationRequest.query.filter_by(user_id=current_user.id).first()
    if vacation:
        return jsonify({
            "sent": True,
            "selected_date": vacation.selected_date.strftime('%Y-%m-%d'),
            "assigned_date": vacation.assigned_date.strftime('%Y-%m-%d')
        })
    return jsonify({"sent": False})

@main.route('/save_vacation_date', methods=['POST'])
@login_required
def save_vacation_date():
    if VacationRequest.query.filter_by(user_id=current_user.username).first():
        return jsonify({"error": "Ya has enviado una fecha. Solo puedes enviarla una vez."}), 400
    data = request.get_json()
    selected_date_str = data.get('selected_date')
    assigned_date_str = data.get('assigned_date')
    if not selected_date_str or not assigned_date_str:
        return jsonify({"error": "Faltan datos de fecha."}), 400
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        assigned_date = datetime.strptime(assigned_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Formato de fecha incorrecto."}), 400
    new_request = VacationRequest(
        user_id=current_user.username,
        selected_date=selected_date,
        assigned_date=assigned_date
    )
    db.session.add(new_request)
    db.session.commit()
    return jsonify({"message": "Fecha guardada exitosamente.", "redirect": "dashboard"})

@main.route('/ver-excel')
def ver_excel():
    excel_path = "static/documentos/calendario.xlsx"
    df = pd.read_excel(excel_path)
    excel_html = df.to_html(classes="table table-striped", index=False)
    return render_template("ver_excel.html", excel_html=excel_html)

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@main.route('/export_competencia_excel')
@login_required
def export_competencia_excel():
    # Obtener todos los registros de la tabla RegistroCompetencia
    registros = RegistroCompetencia.query.all()

    # Crear lista de diccionarios para convertir a DataFrame
    datos = []
    for r in registros:
        datos.append({
            "Número Competidor": r.numero_competidor,
            "User ID": r.user_id,
            "Nombre": r.nombre,
            "Nómina": r.nomina,
            "Turno": r.turno,
            "Categoría": r.categoria,
            "Niños": r.ninos,
            "Adultos": r.adultos,
            "Correo": r.correo,
        })

    # Crear DataFrame
    df = pd.DataFrame(datos)

    # Opcional: reordenar columnas si quieres
    columnas_orden = ["Número Competidor", "User ID", "Nombre", "Nómina", "Turno", "Categoría", "Niños", "Adultos", "Correo"]
    df = df[columnas_orden]

    # Crear archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Registro Competencia')

        # Formato: ajustar ancho columnas
        workbook = writer.book
        worksheet = writer.sheets['Registro Competencia']

        for i, col in enumerate(df.columns):
            # Ajustar ancho con base en la longitud del contenido y el nombre de la columna
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2  # espacio extra
            worksheet.set_column(i, i, max_len)

    output.seek(0)

    # Enviar archivo para descargar
    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name='registro_competencia.xlsx',
                     as_attachment=True)

@main.route('/gestor_contenido', defaults={'folder_id': None})
@main.route('/gestor_contenido/<int:folder_id>')
@login_required
def gestor_contenido(folder_id):
    if folder_id:
        current_folder = Folder.query.get(folder_id)
        files = File.query.filter_by(folder_id=folder_id).all()
        folders = Folder.query.filter_by(parent_id=folder_id).all()
    else:
        current_folder = None
        files = File.query.filter_by(folder_id=None).all()
        folders = Folder.query.filter_by(parent_id=None).all() 
    return render_template('gestor_contenido.html', folders=folders, current_folder=current_folder, files=files)
@main.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')
    folder_id = request.form.get('folder_id')
    if file and folder_id:
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_file = File(filename=filename, folder_id=folder_id)
        db.session.add(new_file)
        db.session.commit()

        return jsonify({'success': True, 'filename': filename})
    return jsonify({'success': False, 'message': 'Faltan datos'}), 400


@main.route('/add_folder', methods=['POST'])
@login_required
def add_folder():
    folder_name = request.form.get('folder_name')
    parent_id = request.form.get('parent_id') or None 
    if not folder_name:
        return jsonify({'success': False, 'message': 'El nombre de la carpeta es obligatorio.'}), 400
    try:
        new_folder = Folder(name=folder_name, parent_id=parent_id)
        db.session.add(new_folder)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Carpeta creada correctamente.'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al crear la carpeta: {str(e)}'}), 500


@main.route('/rename_folder/<int:folder_id>', methods=['POST'])
@login_required
def rename_folder(folder_id):
    folder = Folder.query.get(folder_id)
    if folder:
        data = request.get_json()
        folder.name = data.get('name')
        db.session.commit()
        return jsonify({'success': True, 'message': 'Carpeta renombrada correctamente.'})
    return jsonify({'success': False, 'message': 'Carpeta no encontrada.'}), 404

@main.route('/move_folder/<int:folder_id>', methods=['POST'])
@login_required
def move_folder(folder_id):
    folder = Folder.query.get(folder_id)
    if folder:
        data = request.get_json()
        folder.parent_id = data.get('parent_id')
        db.session.commit()
        return jsonify({'success': True, 'message': 'Carpeta movida correctamente.'})
    return jsonify({'success': False, 'message': 'Carpeta no encontrada.'}), 404

@main.route('/get_all_folders', methods=['GET'])
@login_required
def get_all_folders():
    folders = Folder.query.all() 
    folder_list = [{"id": folder.id, "name": folder.name, "parent_id": folder.parent_id} for folder in folders]
    return jsonify({"success": True, "folders": folder_list})

@main.route('/rename_file/<int:file_id>', methods=['POST'])
@login_required
def rename_file(file_id):
    file = File.query.get(file_id)
    if file:
        data = request.get_json()
        new_name = data.get('new_name')
        if new_name:
            file.filename = new_name
            db.session.commit()
            return jsonify({'success': True, 'message': 'Archivo renombrado correctamente.'})
    return jsonify({'success': False, 'message': 'Archivo no encontrado.'}), 404

@main.route('/add_aviso', methods=['POST'])
@login_required
def add_aviso():
    data = request.get_json()
    descripcion = data.get('descripcion')
    fecha_caducidad = data.get('fecha_caducidad')

    if descripcion:
        aviso = Aviso(
            descripcion=descripcion,
            fecha_caducidad=datetime.strptime(fecha_caducidad, '%Y-%m-%d').date() if fecha_caducidad else None,
            user_id=current_user.id
        )
        db.session.add(aviso)
        db.session.commit()

        return jsonify({
            "success": True,
            "aviso": {
                "descripcion": aviso.descripcion,
                "fecha_caducidad": aviso.fecha_caducidad.strftime('%Y-%m-%d') if aviso.fecha_caducidad else "",
                "fecha_creacion": aviso.fecha_creacion.strftime('%Y-%m-%d %H:%M')
            }
        })
    return jsonify({"success": False}), 400

@main.route('/formulario')
@login_required
def formulario():
    return render_template('formulario.html')

@main.route('/formulario_datos', methods=['GET', 'POST'])
@login_required
def formulario_datos():
    if request.method == 'POST':
        return submit_formulario()
    return render_template('formulario.html')

@main.route('/api/buscar_usuario/<username>')
@login_required
def buscar_usuario(username):
    usuario = User.query.filter_by(username=username).first()
    if usuario:
        return jsonify({
            "success": True,
            "id": usuario.id,
            "nombre": usuario.nombre,
            "puesto": usuario.puesto,
            "turno": usuario.turno or "",
            'estacion': usuario.estacion,
            "nomina": usuario.username,
            "image_file": usuario.image_file or "default.jpg"
        })
    return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
@main.route('/api/listar_usuarios')
@login_required
def listar_usuarios():
    filtros = {
        "COORDINADOR OPERATIVO": ["TENIENTE"],
        "SUBTENIENTE": ["BOMBERO ESPECIALIZADO", "BOMBERO HABILITADO"],
        "TENIENTE": ["SUBTENIENTE"],
    }

    query = User.query.filter(User.id != current_user.id)

    if current_user.puesto in filtros:
        query = query.filter(User.puesto.in_(filtros[current_user.puesto]))

    usuarios = query.all()

    lista = [
        {
            "username": u.username,
            "nombre": u.nombre,
            "turno": u.turno or ""
        }
        for u in usuarios
    ]

    return jsonify({"success": True, "usuarios": lista})

@main.route('/api/listar_usuarios_permitidos')
@login_required
def listar_usuarios_permitidos():
    """API que retorna usuarios que el evaluador actual tiene permiso de evaluar"""
    # Mapeo de permisos: evaluador_id -> [user_ids permitidos]
    PERMISOS_EVALUACION = {
        7: [30, 42, 49],
        263: [101, 111, 182],
        63: [148, 180, 185, 264, 301, 303]
    }
    
    evaluador_id = current_user.id
    usuarios_permitidos_ids = PERMISOS_EVALUACION.get(evaluador_id, [])
    
    if not usuarios_permitidos_ids:
        return jsonify({"success": True, "usuarios": []})
    
    usuarios = User.query.filter(User.id.in_(usuarios_permitidos_ids)).all()
    
    lista = [
        {
            "id": u.id,
            "username": u.username,
            "nombre": u.nombre,
            "turno": u.turno or "N/A",
            "puesto": u.puesto or "N/A"
        }
        for u in usuarios
    ]
    
    return jsonify({"success": True, "usuarios": lista})

@main.route('/api/listado_fotos')
def listado_fotos():
    """Retorna lista de usuarios con URLs de fotos para reconocimiento facial."""
    usuarios = User.query.filter(User.username != 'admin').all()
    import os
    
    usuarios_info = []
    firma_partes = []
    for usuario in usuarios:
        foto_path = os.path.join(current_app.root_path, 'static', 'uploads', f'{usuario.username}.jpg')
        if os.path.exists(foto_path):
            mtime = int(os.path.getmtime(foto_path))
            usuarios_info.append({
                "username": usuario.username,
                "nombre": usuario.nombre,
                "foto_url": url_for('static', filename=f'uploads/{usuario.username}.jpg'),
                "mtime": mtime
            })
            firma_partes.append(f"{usuario.username}:{mtime}")
    
    firma = "|".join(sorted(firma_partes))
    return jsonify({"success": True, "usuarios": usuarios_info, "firma": firma})

def _face_cache_file_path():
    os.makedirs(current_app.instance_path, exist_ok=True)
    return os.path.join(current_app.instance_path, 'face_references_cache.json')


@main.route('/api/face_cache', methods=['GET', 'POST'])
def face_cache():
    usuarios_resp = listado_fotos().get_json()
    current_firma = usuarios_resp.get('firma', '')

    cache_path = _face_cache_file_path()

    if request.method == 'GET':
        if not os.path.exists(cache_path):
            return jsonify({"success": True, "ready": False, "firma": current_firma, "items": []})

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                payload = pyjson.load(f)
        except Exception:
            return jsonify({"success": True, "ready": False, "firma": current_firma, "items": []})

        ready = payload.get('firma') == current_firma and len(payload.get('items', [])) > 0
        return jsonify({
            "success": True,
            "ready": ready,
            "firma": current_firma,
            "items": payload.get('items', []) if ready else []
        })

    body = request.get_json(silent=True) or {}
    incoming_firma = body.get('firma', '')
    items = body.get('items', [])

    if incoming_firma != current_firma:
        return jsonify({"success": False, "error": "Firma desactualizada"}), 409

    if not isinstance(items, list) or len(items) == 0:
        return jsonify({"success": False, "error": "Sin descriptores para guardar"}), 400

    payload = {"firma": current_firma, "items": items}
    with open(cache_path, 'w', encoding='utf-8') as f:
        pyjson.dump(payload, f)

    return jsonify({"success": True})


@main.route('/api/facial_status')
def facial_status():
    """
    Retorna el estado del servicio de reconocimiento facial.
    """
    try:
        from app.facial_service import facial_service
        
        is_ready = (
            facial_service.initialized and 
            facial_service.embeddings_model is not None and
            len(facial_service.face_descriptors) > 0
        )
        
        return jsonify({
            "success": True,
            "ready": is_ready,
            "count": len(facial_service.face_descriptors)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "ready": False,
            "error": str(e)
        }), 500


@main.route('/api/recognize_face', methods=['POST'])
def recognize_face():
    """
    Reconoce un rostro en una imagen enviada como base64.
    Usa el servicio facial precargado en servidor.
    """
    try:
        from app.facial_service import facial_service
        
        if not facial_service.initialized or not facial_service.face_descriptors:
            return jsonify({
                "success": False,
                "error": "Servicio facial no disponible"
            }), 503
        
        body = request.get_json(silent=True) or {}
        image_base64 = body.get('image', '').strip()
        
        if not image_base64:
            return jsonify({
                "success": False,
                "error": "Imagen requerida"
            }), 400
        
        # Decodificar imagen base64
        try:
            import base64
            import cv2
            import numpy as np
            
            # Remover prefijo data:image si existe
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            image_data = base64.b64decode(image_base64)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return jsonify({
                    "success": False,
                    "error": "Imagen inválida"
                }), 400
            
            # Reconocer rostro
            username, nombre, confidence = facial_service.recognize_face(image, threshold=0.5)
            
            if username:
                return jsonify({
                    "success": True,
                    "username": username,
                    "nombre": nombre,
                    "confidence": float(confidence)
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "No se pudo identificar el rostro"
                }), 401
        
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"[Facial] Error decodificando imagen: {e}")
            return jsonify({
                "success": False,
                "error": "Error procesando imagen"
            }), 400
    
    except ImportError:
        return jsonify({
            "success": False,
            "error": "Servicio facial no disponible"
        }), 503
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[Facial] Error en recognize_face: {e}")
        return jsonify({
            "success": False,
            "error": "Error interno del servidor"
        }), 500


@main.route('/api/login_facial', methods=['POST'])
def login_facial():
    body = request.get_json(silent=True) or {}
    username = (body.get('username') or '').strip()
    recaptcha_token = (body.get('recaptcha_token') or '').strip()

    if not username:
        return jsonify({"success": False, "error": "Usuario requerido"}), 400

    verified_at = session.get('facial_captcha_verified_at')
    captcha_ok = False

    if verified_at:
        if datetime.utcnow().timestamp() - float(verified_at) <= 300:
            captcha_ok = True
        else:
            session.pop('facial_captcha_verified_at', None)

    if not captcha_ok:
        if not recaptcha_token:
            return jsonify({"success": False, "error": "Captcha facial no verificado"}), 403

        secret_key = current_app.config.get('RECAPTCHA_PRIVATE_KEY')
        if not secret_key:
            return jsonify({"success": False, "error": "Configuracion de captcha no disponible"}), 500

        try:
            verify_resp = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': secret_key,
                    'response': recaptcha_token,
                    'remoteip': request.remote_addr
                },
                timeout=8
            )
            verify_data = verify_resp.json()
        except Exception:
            return jsonify({"success": False, "error": "No se pudo validar captcha"}), 502

        if not verify_data.get('success'):
            return jsonify({"success": False, "error": "Captcha invalido o expirado"}), 403

    session.pop('facial_captcha_verified_at', None)

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

    if user.username == 'admin':
        return jsonify({"success": False, "error": "Admin requiere contrasena"}), 403

    login_user(user)
    return jsonify({"success": True, "redirect": url_for('main.dashboard')})


@main.route('/api/verify_facial_captcha', methods=['POST'])
def verify_facial_captcha():
    body = request.get_json(silent=True) or {}
    recaptcha_token = (body.get('recaptcha_token') or '').strip()

    if not recaptcha_token:
        return jsonify({"success": False, "error": "Captcha requerido"}), 400

    secret_key = current_app.config.get('RECAPTCHA_PRIVATE_KEY')
    if not secret_key:
        return jsonify({"success": False, "error": "Configuracion de captcha no disponible"}), 500

    try:
        verify_resp = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': secret_key,
                'response': recaptcha_token,
                'remoteip': request.remote_addr
            },
            timeout=8
        )
        verify_data = verify_resp.json()
    except Exception:
        return jsonify({"success": False, "error": "No se pudo validar captcha"}), 502

    if not verify_data.get('success'):
        return jsonify({"success": False, "error": "Captcha invalido o expirado"}), 403

    session['facial_captcha_verified_at'] = datetime.utcnow().timestamp()
    return jsonify({"success": True})

@main.route('/evaluacion_del_desempeño')
@login_required
def evaluacion():

    if current_user.id in [7, 263, 63]:
        return render_template('evaluacion_personal.html', usuario_actual=current_user)

    elif current_user.puesto == "SUBTENIENTE":
        return render_template('evaluacion_subteniente.html', usuario_actual=current_user)

    elif current_user.puesto == "TENIENTE":
        return render_template('evaluacion_teniente.html', usuario_actual=current_user)

    elif current_user.puesto == "COORDINADOR OPERATIVO":
        return render_template('evaluacion_coordinador.html', usuario_actual=current_user)

    else:
        flash('No tienes permiso para acceder a evaluaciones', 'warning')
        return redirect(url_for('main.dashboard'))

@main.route('/evaluacion_personal')
@login_required
def evaluacion_personal():
    """Ruta para evaluación personal con permisos específicos"""
    # Mapeo de permisos: evaluador_id -> [user_ids permitidos]
    PERMISOS_EVALUACION = {
        7: [30, 42, 49],
        263: [101, 111, 182],
        63: [148, 180, 185, 264, 301, 303]
    }
    
    evaluador_id = current_user.id
    
    # Verificar que el usuario tiene permisos para evaluar
    if evaluador_id not in PERMISOS_EVALUACION:
        flash('No tienes permisos para realizar evaluaciones personales', 'warning')
        return redirect(url_for('main.dashboard'))
    
    return render_template('evaluacion_personal.html', usuario_actual=current_user)

@main.route('/findeaño12w')
@login_required
def fin_anio():
    respuesta_existente = AsistenciaFinAnio.query.filter_by(user_id=current_user.id).first()
    if respuesta_existente:
        return render_template('dashboard.html', ya_respondio=True, registro=respuesta_existente)
    else:
        return render_template('dia_bombero.html', ya_respondio=False)

@main.route('/competencia_bomb')
@login_required
def competencia_bomb():
    registro_existente = RegistroCompetencia.query.filter_by(user_id=current_user.id).first()

    if registro_existente:
        return render_template('dashboard.html', ya_respondio=True)
    return render_template('competencia_bomb.html')

@main.route('/scanner_asistencia')
@login_required
def scanner_asistencia():
    respuestas_confirmadas = Respuesta.query.filter_by(respondido=True).all()
    return render_template('scanner.html', respuestas_confirmadas=respuestas_confirmadas)

@main.route('/api/marcar_asistencia', methods=['POST'])
@login_required
def marcar_asistencia():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "user_id no proporcionado"}), 400
    
    print(f"Recibido user_id: {user_id}")
    respuesta = Respuesta.query.filter_by(user_id=user_id, respondido=True).first()

    if not respuesta:
        print(f"No se encontró la respuesta para user_id: {user_id}")
        return jsonify({"success": False, "error": "Usuario no encontrado o no respondido"}), 400

    if not respuesta.asistio:
        respuesta.asistio = True
        db.session.commit()
        print(f"Asistencia confirmada para: {respuesta.user.nombre}")
        return jsonify({"success": True, "nombre": respuesta.user.nombre, "nuevo_registro": True}), 200
    else:
        print(f"El usuario ya estaba registrado como asistido para user_id: {user_id}")
        return jsonify({"success": True, "nombre": respuesta.user.nombre, "nuevo_registro": False}), 200
@main.route('/submit_bombero', methods=['POST'])
@login_required
def submit_bombero():
    nombre = current_user.nombre
    acompanante = request.form.get("lleva_acompanante")
    nombre_acompanante = request.form.get("nombre_acompanante")
    tipo_acompanante = request.form.get("tipo_acompanante")  # NUEVO CAMPO
    correo = request.form.get("correo")

    respuesta = Respuesta.query.filter_by(user_id=current_user.id).first()
    if not respuesta:
        respuesta = Respuesta(user_id=current_user.id)

    respuesta.nombre_acompanante = nombre_acompanante
    respuesta.tipo_acompanante = tipo_acompanante  # Guardar el tipo
    respuesta.correo = correo
    respuesta.respondido = True

    db.session.add(respuesta)
    db.session.commit()

    contenido_qr = f"{current_user.id}\nAsistencia confirmada:\n{nombre}"
    if acompanante == "sí":
        contenido_qr += f"\nAcompañante: {nombre_acompanante}"
        if tipo_acompanante:
            contenido_qr += f" ({tipo_acompanante})"
    contenido_qr += f"\nCorreo: {correo}"

    qr = qrcode.make(contenido_qr)
    filename = f"{nombre.replace(' ', '_')}_qr.png"
    carpeta_qr = os.path.join(os.getcwd(), 'app', 'qr_codes')
    os.makedirs(carpeta_qr, exist_ok=True)
    filepath = os.path.join(carpeta_qr, filename)
    qr.save(filepath)

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; text-align: center;">
            <div style="max-width: 600px; margin: auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #d32f2f;">🎉 Confirmación de Asistencia</h2>
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Gracias por confirmar tu asistencia al <strong>Día del Bombero</strong>.</p>
                <p><strong>Este es tu pase de entrada</strong>. Presenta este código QR al ingresar al evento:</p>
                <img src="cid:{filename}" style="margin-top: 20px; width: 250px; height: auto;" alt="QR Code" />
                <p style="margin-top: 20px; font-size: 0.9rem; color: #555;">⚠️ Sin este pase no podrás acceder al evento. Por favor, no lo pierdas.</p>
                <p style="margin-top: 30px;">¡Te esperamos! 👨‍🚒</p>
            </div>
        </body>
    </html>
    """

    msg = Message("🎫 Tu pase para el Día del Bombero",
                sender="cristian.rodriguez@bomberosdeleon.org",
                recipients=[correo])

    msg.body = f"Hola {nombre}, adjunto encontrarás tu código QR para el evento."
    msg.html = html_body

    with open(filepath, 'rb') as fp:
        msg.attach(filename, "image/png", fp.read(), headers={"Content-ID": f"<{filename}>"})

    mail.send(msg)

    return render_template('confirmation.html', nombre=nombre, correo=correo)

import io
import pandas as pd
from flask import send_file

@main.route('/descargar_registros_excel', methods=['GET'])
@login_required
def descargar_registros_excel():
    # Obtener todos los registros
    registros = Respuesta.query.all()

    # Preparar los datos para el DataFrame
    data = []
    for r in registros:
        tiene_acompanante = bool(r.nombre_acompanante and r.nombre_acompanante.strip())
        data.append({
            "Nombre": r.user.nombre if r.user else "Desconocido",
            "Correo": r.correo,
            "Acompañante": r.nombre_acompanante if tiene_acompanante else "",
            "Tipo Acompañante": r.tipo_acompanante if tiene_acompanante else "",
            "Con Acompañante": "Sí" if tiene_acompanante else "No"
        })

    # Crear el DataFrame
    df = pd.DataFrame(data)

    # Escribir a un archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Participantes', index=False)
        workbook  = writer.book
        worksheet = writer.sheets['Participantes']

        # Estilo para resaltar en amarillo
        highlight_format = workbook.add_format({'bg_color': '#FFFF00'})

        # Aplicar formato a filas con acompañante
        for i, row in df.iterrows():
            if row['Con Acompañante'] == 'Sí':
                worksheet.set_row(i + 1, None, highlight_format)  # +1 por encabezado

    output.seek(0)

    return send_file(output,
                     download_name="registros_bombero.xlsx",
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@main.route('/submit_competencia', methods=['POST'])
@login_required
def submit_competencia():
    nombre = request.form.get('nombre')
    nomina = request.form.get('nomina')
    turno = request.form.get('turno')
    categoria = request.form.get('categoria')
    ninos = int(request.form.get('ninos', 0))
    adultos = int(request.form.get('adultos', 0))
    correo = request.form.get('correo')
    registro = RegistroCompetencia.query.filter_by(user_id=current_user.id).first()

    if not registro:
        ultimo_num = db.session.query(db.func.max(RegistroCompetencia.numero_competidor)).scalar()
        nuevo_num = 1 if ultimo_num is None else ultimo_num + 1

        registro = RegistroCompetencia(
            user_id=current_user.id,
            nombre=nombre,
            nomina=nomina,
            turno=turno,
            categoria=categoria,
            ninos=ninos,
            adultos=adultos,
            numero_competidor=nuevo_num,
            correo=correo
        )
        db.session.add(registro)
        db.session.commit()
    else:
        nuevo_num = registro.numero_competidor

    from flask_mail import Message

    texto = f"Hola {nombre},\n\nGracias por registrarte al Bombero Challenge.\nTu número de competidor es: #{nuevo_num}.\n\n¡Te esperamos!"

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
        <h2 style="color: #d32f2f;">🎉 Confirmación de Competencia</h2>
        <p>Hola <strong>{nombre}</strong>,</p>
        <p>Gracias por registrarte al <strong>Bombero Challenge</strong>.</p>
        <p><strong>Tu número de competidor es: #{nuevo_num}</strong></p>
        <p>¡Te esperamos! 👨‍🚒</p>
      </body>
    </html>
    """

    msg = Message(subject="🎫 Confirmación Bombero Challenge",
                  sender="cristian.rodriguez@bomberosdeleon.org",
                  recipients=[correo])

    msg.body = texto
    msg.html = html

    mail.send(msg)

    return render_template('confirmation_competencia.html', nombre=nombre, correo=correo, numero=nuevo_num)


@main.route('/submit_formulario', methods=['POST'])
def submit_formulario():
    try:
        preguntas = [
            'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 
            'q9', 'q10', 'q11', 'q12', 'q13', 'q14', 'q15', 'q16', 
            'q17', 'q18', 'q19', 'q20', 'q21', 'q22', 'q23', 'q24', 
            'q25', 'q26', 'q27', 'q28', 'q29', 'q30', 'q31', 'q32', 
            'q33', 'q34', 'q35', 'q36', 'q37', 'q38', 'q39', 'q40', 
            'q41', 'q42', 'q43', 'q44', 'q45', 'q46', 'q47', 'q48', 
            'q49', 'q50', 'q51', 'q52', 'q53', 'q54', 'q55', 'q56', 
            'q57', 'q58', 'q59', 'q60', 'q61', 'q62', 'q63', 'q64'
        ]
        respuestas = {}
        for pregunta in preguntas:
            respuesta = request.form.get(pregunta)
            if respuesta:
                respuestas[pregunta] = int(respuesta) 
        nueva_respuesta = FormularioRespuesta(
            usuario_id=current_user.id,
            respuestas=json.dumps(respuestas),  
            fecha_creacion=datetime.now()
        )
        db.session.add(nueva_respuesta)
        db.session.commit()
        flash("¡Formulario enviado correctamente!", "success")
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al enviar el formulario: {e}", "danger")
        return redirect(url_for('main.dashboard'))
@main.route('/add_evento', methods=['POST'])
@login_required
def add_evento():
    data = request.get_json()
    descripcion = data.get("descripcion")
    fecha = data.get("fecha")

    if descripcion and fecha:
        evento = Evento(
            descripcion=descripcion,
            fecha=datetime.strptime(fecha, "%Y-%m-%d").date(),
            user_id=current_user.id
        )
        db.session.add(evento)
        db.session.commit()
        return jsonify({"success": True, "evento_id": evento.id})

    return jsonify({"success": False}), 400

@main.route('/delete_evento/<int:evento_id>', methods=['DELETE'])
@login_required
def delete_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    db.session.delete(evento)
    db.session.commit()
    return jsonify({ "success": True })

@main.route('/admin/noticias', methods=['GET', 'POST'])
@login_required
def admin_noticias():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        imagen = request.files['imagen']
        link = request.form.get('link')

        if imagen:
            imagen.save(f"app/static/img/{imagen.filename}")

        nueva_noticia = Noticia(
            titulo=titulo,
            descripcion=descripcion,
            imagen=imagen.filename,
            link=link
        )
        db.session.add(nueva_noticia)
        db.session.commit()
        return redirect(url_for('main.admin_noticias'))

    noticias = Noticia.query.all()
    return render_template('admin_noticias.html', noticias=noticias)

@main.route('/admin/noticias/delete/<int:id>', methods=['GET', 'DELETE'])
@login_required
def delete_noticia(id):
    try:
        noticia = Noticia.query.get_or_404(id)
        db.session.delete(noticia)
        db.session.commit()
        if request.method == 'DELETE':
            return jsonify({'success': True, 'message': 'Noticia eliminada correctamente'})
        flash('Noticia eliminada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        if request.method == 'DELETE':
            return jsonify({'success': False, 'message': str(e)}), 500
        flash(f'Error al eliminar noticia: {str(e)}', 'error')
    return redirect(url_for('main.admin_noticias'))
@main.route('/delete_file/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    try:
        file_record = File.query.filter_by(filename=filename).first()
        if not file_record:
            return jsonify({'success': False, 'message': 'Archivo no encontrado'}), 404

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        db.session.delete(file_record)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/list_files')
@login_required
def list_files():
    files = File.query.with_entities(File.filename).all()
    filenames = [f[0] for f in files]
    return jsonify({'files': filenames})

@main.route('/delete_aviso/<int:aviso_id>', methods=['POST'])
@login_required
def delete_aviso(aviso_id):
    if current_user.id != 2:
        return jsonify({'success': False, 'message': 'No tienes permiso para eliminar avisos.'}), 403
    
    aviso = Aviso.query.get_or_404(aviso_id)
    db.session.delete(aviso)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Aviso eliminado correctamente.'})


@main.route('/move_noticia/<int:id>/<string:direction>')
@login_required
def move_noticia(id, direction):
    noticia = Noticia.query.get_or_404(id)

    if direction == 'up':
        noticia_superior = Noticia.query.filter(Noticia.orden < noticia.orden).order_by(Noticia.orden.desc()).first()
        if noticia_superior:
            noticia.orden, noticia_superior.orden = noticia_superior.orden, noticia.orden

    elif direction == 'down':
        noticia_inferior = Noticia.query.filter(Noticia.orden > noticia.orden).order_by(Noticia.orden.asc()).first()
        if noticia_inferior:
            noticia.orden, noticia_inferior.orden = noticia_inferior.orden, noticia.orden

    db.session.commit()
    return redirect(url_for('main.admin_noticias'))

@main.route('/agregar_portal', methods=['POST'])
@login_required
def agregar_portal():
    if current_user.id == 2:
        nombre = request.form.get('nombre')
        url = request.form.get('url')
        if nombre and url:
            nuevo_portal = PortalWeb(nombre=nombre, url=url)
            db.session.add(nuevo_portal)
            db.session.commit()
            return jsonify({"success": True})
    return jsonify({"success": False}), 403


@main.route('/eliminar_portal', methods=['POST'])
@login_required
def eliminar_portal():
    import sys
    try:
        print(f"DEBUG eliminar_portal: user_id={current_user.id}", file=sys.stderr)
        print(f"DEBUG eliminar_portal: request.json={request.json}", file=sys.stderr)
        if current_user.id == 2:
            portal_id = request.json.get('id')
            print(f"DEBUG eliminar_portal: portal_id={portal_id}", file=sys.stderr)
            portal = PortalWeb.query.get(portal_id)
            if portal:
                db.session.delete(portal)
                db.session.commit()
                print(f"DEBUG eliminar_portal: eliminado portal_id={portal_id}", file=sys.stderr)
                return jsonify({"success": True})
            else:
                print(f"DEBUG eliminar_portal: portal no encontrado id={portal_id}", file=sys.stderr)
        else:
            print(f"DEBUG eliminar_portal: usuario no autorizado id={current_user.id}", file=sys.stderr)
        return jsonify({"success": False}), 403
    except Exception as e:
        import traceback
        print(f"ERROR eliminar_portal: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({"success": False, "error": str(e)}), 500


@main.route('/guardar_contacto', methods=['POST'])
@login_required
def guardar_contacto():

    try:
        nombre = request.form['nombre_contacto']
        parentesco = request.form['parentesco']
        telefono = request.form['telefono_contacto']
        calle = request.form['calle_numero']
        colonia = request.form['colonia']
        otro = request.form.get('otro_parentesco')

        contacto_existente = ContactoEmergencia.query.filter_by(
            user_id=current_user.id
        ).first()

        if contacto_existente:
            # Actualiza si ya existe registro
            contacto_existente.username = current_user.username
            contacto_existente.nombre_contacto = nombre
            contacto_existente.parentesco = parentesco
            contacto_existente.telefono_contacto = telefono
            contacto_existente.calle_numero = calle
            contacto_existente.colonia = colonia
            contacto_existente.otro_parentesco = otro

            mensaje = "Contacto de emergencia actualizado correctamente"

        else:
            # Crea nuevo registro
            nuevo_contacto = ContactoEmergencia(
                user_id=current_user.id,
                username=current_user.username,
                nombre_contacto=nombre,
                parentesco=parentesco,
                telefono_contacto=telefono,
                calle_numero=calle,
                colonia=colonia,
                otro_parentesco=otro
            )

            db.session.add(nuevo_contacto)

            mensaje = "Contacto de emergencia registrado correctamente"

        db.session.commit()

        flash(mensaje, "success")

        return redirect(url_for('main.dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error al guardar el contacto: {str(e)}", "danger")
        return redirect(url_for('main.dashboard'))


@main.route('/check_admin')
def check_admin():
    """Verifica si el usuario actual es administrador"""
    is_admin = current_user.is_authenticated and current_user.id == 2
    return jsonify({"is_admin": is_admin})


@main.route('/export_contactos_excel')
@login_required
def export_contactos_excel():
    """Exporta todos los contactos de emergencia a un archivo Excel"""
    try:
        # Verificar permisos de admin
        if current_user.id != 2:
            return jsonify({"error": "No tienes permisos para descargar este archivo"}), 403
        
        # Obtener todos los contactos
        contactos = ContactoEmergencia.query.all()
        
        # Preparar datos para Excel
        datos = []
        for contacto in contactos:
            usuario = User.query.get(contacto.user_id)
            
            # Determinar parentesco completo
            parentesco_completo = contacto.parentesco
            if contacto.parentesco == "Otro" and contacto.otro_parentesco:
                parentesco_completo = f"Otro ({contacto.otro_parentesco})"
            
            datos.append({
                'Nombre del Empleado': usuario.nombre if usuario else 'N/A',
                'Username': contacto.username,
                'Turno': usuario.turno if usuario else 'N/A',
                'Puesto': usuario.puesto if usuario else 'N/A',
                'Nombre del Contacto': contacto.nombre_contacto,
                'Parentesco': parentesco_completo,
                'Teléfono': contacto.telefono_contacto,
                'Calle y Número': contacto.calle_numero,
                'Colonia': contacto.colonia,
                'Fecha de Registro': contacto.fecha_registro.strftime('%Y-%m-%d %H:%M:%S') if contacto.fecha_registro else 'N/A'
            })
        
        # Crear DataFrame
        df = pd.DataFrame(datos)
        
        # Crear archivo Excel con formato
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Contactos', index=False)
            
            # Aplicar estilos
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            
            workbook = writer.book
            worksheet = writer.sheets['Contactos']
            
            # Estilos
            header_fill = PatternFill(start_color="2563eb", end_color="2563eb", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=12)
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # Aplicar estilos al encabezado
            for col_num, value in enumerate(df.columns, 1):
                cell = worksheet.cell(row=1, column=col_num)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
            # Aplicar bordes y ajustar ancho de columnas
            for col_num, col in enumerate(df.columns, 1):
                col_letter = openpyxl.utils.get_column_letter(col_num)
                max_length = 0
                
                for cell in worksheet[col_letter]:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                        cell.border = thin_border
                        cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
                    except:
                        pass
                
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[col_letter].width = min(adjusted_width, 50)
        
        output.seek(0)
        
        # Enviar archivo
        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Contactos_Emergencia_{fecha}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logging.error(f"Error al exportar contactos a Excel: {str(e)}")
        return jsonify({"error": f"Error al descargar: {str(e)}"}), 500