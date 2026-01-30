import datetime
from flask_mail import Mail, Message
import pandas as pd
from flask import Blueprint, current_app, json, jsonify, render_template, request, redirect, session, url_for, send_from_directory, flash, send_file 
from flask_login import current_user, login_user, logout_user, login_required
import qrcode
from werkzeug.utils import secure_filename
from app import db
from io import BytesIO # Necesario para manejar el archivo en memoria
import os
from app.models import Aviso, Evento, File, Folder, FormularioRespuesta, PortalWeb, Respuesta, User, VacationRequest, Noticia, RegistroCompetencia, EvaluacionDesempeno, AsistenciaFinAnio
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
    allowed_ids = [304]  # IDs autorizados
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

        # Calcular promedio general y por rubro
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

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: 
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)

            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html', form=form)
from flask import session

@main.route('/change_password', methods=['POST'])
@login_required
def change_password():
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    if new_password != confirm_password:
        flash('Las contraseñas no coinciden.', 'danger')
        return redirect(url_for('main.dashboard'))

    current_user.set_password(new_password)
    current_user.password_changed = True
    db.session.commit()

    with open('cambio_contraseñas.txt', 'a', encoding='utf-8') as f:
        f.write(f"Usuario: {current_user.username} - Nueva contraseña: {new_password}\n")

    session['show_password_changed_message'] = True

    return redirect(url_for('main.dashboard'))

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('main.login'))

@main.route('/submit_evaluacion', methods=['POST'])
@login_required
def submit_evaluacion():
    # Recibimos las respuestas del formulario
    nombre = request.form.get('nombre')
    fecha_str = request.form.get('fecha')
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    area = request.form.get('area')
    estacion = request.form.get('estacion')
    nomina = request.form.get('nomina')
    puesto = request.form.get('puesto')
    
    # Almacenamos las respuestas del formulario en un diccionario
    respuestas = {
        'desempeno': {
            'q1': request.form.get('q1'),
            'q2': request.form.get('q2'),
            'q3': request.form.get('q3'),
            'q4': request.form.get('q4'),
            'q5': request.form.get('q5'),
            'q6': request.form.get('q6')
        },
        'jefe_inmediato': {
            'q7': request.form.get('q7'),
            'q8': request.form.get('q8'),
            'q9': request.form.get('q9'),
            'q10': request.form.get('q10'),
            'q11': request.form.get('q11'),
            'q12': request.form.get('q12')
        },
        'apoyo_convivencia': {
            'q13': request.form.get('q13'),
            'q14': request.form.get('q14'),
            'q15': request.form.get('q15'),
            'q16': request.form.get('q16'),
            'q17': request.form.get('q17'),
            'q18': request.form.get('q18')
        },
        'pertenencia': {
            'q19': request.form.get('q19'),
            'q20': request.form.get('q20'),
            'q21': request.form.get('q21'),
            'q22': request.form.get('q22'),
            'q23': request.form.get('q23'),
            'q24': request.form.get('q24')
        },
        'clasificacion': {
            'q25': request.form.get('q25'),
            'q26': request.form.get('q26'),
            'q27': request.form.get('q27'),
            'q28': request.form.get('q28'),
            'q29': request.form.get('q29'),
            'q30': request.form.get('q30'),
            'q31': request.form.get('q31'),
            'q32': request.form.get('q32'),
            'q33': request.form.get('q33'),
            'q34': request.form.get('q34'),
            'q35': request.form.get('q35'),
            'q36': request.form.get('q36'),
            'q37': request.form.get('q37'),
            'q38': request.form.get('q38'),
            'q39': request.form.get('q39'),
            'q40': request.form.get('q40'),
            'q41': request.form.get('q41'),
            'q42': request.form.get('q42'),
            'q43': request.form.get('q43'),
            'q44': request.form.get('q44')
        }
    }

    evaluacion_general = request.form.get('evaluacion_general')
    comentario = request.form.get('comentario')

    # Crear un objeto de la evaluación
    evaluacion = EvaluacionDesempeno(
        user_id=current_user.id,
        nombre=nombre,
        fecha=fecha,
        area=area,
        estacion=estacion,
        nomina=nomina,
        puesto=puesto,
        respuestas=respuestas,
        evaluacion_general=evaluacion_general,
        comentario=comentario
    )

    # Guardar la evaluación en la base de datos
    db.session.add(evaluacion)
    db.session.commit()

    flash("Formulario enviado con éxito", "success")  # Mostrar un mensaje de éxito

    # Redirigir al dashboard
    return redirect(url_for('main.dashboard'))


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

@main.route('/evaluacion_del_desempeño')
@login_required
def evaluacion():
    return render_template('evaluacion.html')

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

    # Verificar si ya hay un registro para este usuario
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

    # Cuerpo simple de texto y HTML sin QR
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
        return redirect(url_for('main.index'))
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

@main.route('/admin/noticias/delete/<int:id>')
def delete_noticia(id):
    noticia = Noticia.query.get_or_404(id)
    db.session.delete(noticia)
    db.session.commit()
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


