from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.dialects.sqlite import JSON
from werkzeug.security import generate_password_hash, check_password_hash
import requests

from app import db 
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    image_file = db.Column(db.String(100), nullable=False, default='default.jpg')
    password_changed = db.Column(db.Boolean, default=False)
    turno = db.Column(db.String(30))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class VacationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    selected_date = db.Column(db.Date, nullable=False)
    assigned_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('vacation_request', uselist=False))
class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)

    parent = db.relationship('Folder', remote_side=[id], backref=db.backref('subfolders', lazy=True))

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)

    folder = db.relationship('Folder', backref=db.backref('files', lazy=True))

class Aviso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(255), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_caducidad = db.Column(db.Date, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    usuario = db.relationship('User', backref=db.backref('avisos', lazy=True))

class FormularioRespuesta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    respuestas = db.Column(db.Text, nullable=False)  
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(255), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    usuario = db.relationship('User', backref=db.backref('eventos', lazy=True))


class Noticia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    imagen = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    orden = db.Column(db.Integer, nullable=False, default=0)  

def get_favicon(url):
    try:
        test_favicon = f"{url.rstrip('/')}/favicon.ico"
        response = requests.get(test_favicon, timeout=3)
        if response.status_code == 200:
            return test_favicon
    except requests.exceptions.RequestException:
        pass
    return f"https://www.google.com/s2/favicons?sz=64&domain={url}"

class PortalWeb(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    favicon = db.Column(db.String(255), nullable=True)

def __init__(self, nombre, url):
    self.nombre = nombre
    self.url = url
    self.favicon = f"https://www.google.com/s2/favicons?sz=64&domain={url}"


class Respuesta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nombre_acompanante = db.Column(db.String(100))
    tipo_acompanante = db.Column(db.String(20))  # NUEVO CAMPO
    correo = db.Column(db.String(100), nullable=False)
    respondido = db.Column(db.Boolean, default=False)
    asistio = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('respuestas', lazy=True))

    def __repr__(self):
        return f'<Respuesta {self.id}>'


class RegistroCompetencia(db.Model):
    __tablename__ = 'registro_competencia'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nombre = db.Column(db.String, nullable=False)
    nomina = db.Column(db.String, nullable=False)
    turno = db.Column(db.String(1), nullable=False)
    categoria = db.Column(db.String(20), nullable=False)
    ninos = db.Column(db.Integer, default=0)
    adultos = db.Column(db.Integer, default=0)
    numero_competidor = db.Column(db.Integer, unique=True, nullable=False)
    correo = db.Column(db.String, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='registros_competencia')

class EvaluacionDesempeno(db.Model):
    __tablename__ = 'evaluacion_desempeno'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    area = db.Column(db.String(100), nullable=False)
    estacion = db.Column(db.String(100), nullable=False)
    nomina = db.Column(db.String(20), nullable=False)
    puesto = db.Column(db.String(100), nullable=False)
    respuestas = db.Column(db.JSON, nullable=False)  # Almacenamos las respuestas en formato JSON
    evaluacion_general = db.Column(db.String(20), nullable=False)
    comentario = db.Column(db.String(500), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('evaluaciones_desempeno', lazy=True))

    def __repr__(self):
        return f'<EvaluacionDesempeno {self.id}>'

class AsistenciaFinAnio(db.Model):
    __tablename__ = 'asistencia_fin_anio'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    nombre_usuario = db.Column(db.String(100), nullable=False)
    asistencia = db.Column(db.String(5), nullable=False)        
    lleva_acompanante = db.Column(db.String(5), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship('User', backref='asistencia_evento', uselist=False)
