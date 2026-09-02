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
    puesto = db.Column(db.String(50))
    estacion = db.Column(db.String(50))
    ultima_actividad = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AreaCompra(db.Model):
    """Catálogo y contador independiente para órdenes de compra por área."""
    __tablename__ = 'area_compra'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    codigo = db.Column(db.String(12), nullable=False, unique=True)
    ultimo_consecutivo = db.Column(db.Integer, nullable=False, default=0)
    activa = db.Column(db.Boolean, nullable=False, default=True)


class ProveedorCompra(db.Model):
    __tablename__ = 'proveedor_compra'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(160), nullable=False, unique=True, index=True)
    domicilio = db.Column(db.String(300), nullable=True)
    atencion_a = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(40), nullable=True)
    rfc = db.Column(db.String(20), nullable=True)
    correo = db.Column(db.String(160), nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class PartidaPresupuestal(db.Model):
    __tablename__ = 'partida_presupuestal'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), nullable=False, unique=True, index=True)
    nombre = db.Column(db.String(180), nullable=False)
    descripcion = db.Column(db.String(300), nullable=True)
    activa = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class OrdenCompra(db.Model):
    __tablename__ = 'orden_compra'
    id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(db.Integer, db.ForeignKey('area_compra.id'), nullable=False, index=True)
    consecutivo = db.Column(db.Integer, nullable=False)
    folio = db.Column(db.String(40), nullable=False, unique=True, index=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False)
    fecha_entrega_requerida = db.Column(db.Date, nullable=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor_compra.id'), nullable=True, index=True)
    partida_presupuestal_id = db.Column(db.Integer, db.ForeignKey('partida_presupuestal.id'), nullable=True, index=True)
    proveedor = db.Column(db.String(160), nullable=False)
    domicilio = db.Column(db.String(300), nullable=True)
    atencion_a = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(40), nullable=True)
    cuenta_presupuestal = db.Column(db.String(180), nullable=False)
    proyecto_programa = db.Column(db.String(180), nullable=True)
    fuente_financiamiento = db.Column(db.String(40), nullable=False, default='RECURSOS PROPIOS')
    tipo_compra = db.Column(db.String(40), nullable=False, default='ADQUISICIÓN DIRECTA')
    justificacion = db.Column(db.Text, nullable=False)
    iva_porcentaje = db.Column(db.Numeric(5, 2), nullable=False, default=16)
    estado = db.Column(db.String(20), nullable=False, default='BORRADOR')
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    area = db.relationship('AreaCompra', backref=db.backref('ordenes', lazy=True))
    solicitante = db.relationship('User', backref=db.backref('ordenes_compra', lazy=True))
    proveedor_catalogo = db.relationship('ProveedorCompra', backref=db.backref('ordenes', lazy=True))
    partida_presupuestal = db.relationship('PartidaPresupuestal', backref=db.backref('ordenes', lazy=True))
    __table_args__ = (
        db.UniqueConstraint('area_id', 'consecutivo', name='uq_orden_area_consecutivo'),
    )

    @property
    def subtotal(self):
        return sum((item.subtotal for item in self.partidas), 0)

    @property
    def iva(self):
        return self.subtotal * self.iva_porcentaje / 100

    @property
    def total(self):
        return self.subtotal + self.iva


class PartidaOrdenCompra(db.Model):
    __tablename__ = 'partida_orden_compra'
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('orden_compra.id', ondelete='CASCADE'), nullable=False, index=True)
    posicion = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Numeric(12, 2), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio_unitario = db.Column(db.Numeric(14, 2), nullable=False)

    orden = db.relationship(
        'OrdenCompra',
        backref=db.backref('partidas', lazy=True, cascade='all, delete-orphan', order_by='PartidaOrdenCompra.posicion'),
    )

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


class FacturaOrdenCompra(db.Model):
    __tablename__ = 'factura_orden_compra'
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('orden_compra.id', ondelete='CASCADE'), nullable=False, index=True)
    nombre_original = db.Column(db.String(255), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False, unique=True)
    tipo_mime = db.Column(db.String(100), nullable=True)
    tamano = db.Column(db.Integer, nullable=False)
    subido_por_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    orden = db.relationship('OrdenCompra', backref=db.backref('facturas', lazy=True, cascade='all, delete-orphan'))
    subido_por = db.relationship('User', backref=db.backref('facturas_compra_subidas', lazy=True))


class PasskeyCredential(db.Model):
    __tablename__ = 'passkey_credential'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    credential_id = db.Column(db.LargeBinary, unique=True, nullable=False)
    public_key = db.Column(db.LargeBinary, nullable=False)
    sign_count = db.Column(db.Integer, nullable=False, default=0)
    nombre_dispositivo = db.Column(db.String(100), nullable=False, default='Dispositivo personal')
    transports = db.Column(db.String(100), nullable=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ultimo_uso = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('passkeys', lazy=True, cascade='all, delete-orphan'))


class EntregaUniforme(db.Model):
    __tablename__ = 'entrega_uniforme'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    prenda = db.Column(db.String(80), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    observaciones = db.Column(db.String(250), nullable=True)
    fecha_entrega = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='entregas_uniformes')


class EntregaGeneralUniforme(db.Model):
    """Entrega de la nueva dotación del personal por un usuario designado."""
    __tablename__ = 'entrega_general_uniforme'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    receptor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    entregado_por_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prenda = db.Column(db.String(80), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    detalle = db.Column(db.String(250), nullable=True)
    fecha_entrega = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    receptor = db.relationship(
        'User', foreign_keys=[receptor_id],
        backref=db.backref('nuevos_uniformes_recibidos', lazy=True)
    )
    entregado_por = db.relationship(
        'User', foreign_keys=[entregado_por_id],
        backref=db.backref('nuevos_uniformes_entregados', lazy=True)
    )


class MensajeChat(db.Model):
    __tablename__ = 'mensaje_chat'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    remitente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    contenido = db.Column(db.String(1000), nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    leido_en = db.Column(db.DateTime, nullable=True)
    editado_en = db.Column(db.DateTime, nullable=True)

    remitente = db.relationship(
        'User', foreign_keys=[remitente_id],
        backref=db.backref('mensajes_chat_enviados', lazy=True)
    )
    destinatario = db.relationship(
        'User', foreign_keys=[destinatario_id],
        backref=db.backref('mensajes_chat_recibidos', lazy=True)
    )


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
    usuarios_permitidos = db.relationship(
        'User',
        secondary='portal_web_usuario',
        lazy='select',
        backref=db.backref('portales_permitidos', lazy='dynamic')
    )


class PortalWebUsuario(db.Model):
    __tablename__ = 'portal_web_usuario'
    portal_id = db.Column(db.Integer, db.ForeignKey('portal_web.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Quien es evaluado
    evaluador_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Quien evalúa
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

    # Relaciones
    usuario_evaluado = db.relationship('User', foreign_keys=[user_id], backref=db.backref('evaluaciones_recibidas', lazy=True))
    usuario_evaluador = db.relationship('User', foreign_keys=[evaluador_id], backref=db.backref('evaluaciones_realizadas', lazy=True))

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


class PermisosEvaluacion(db.Model):
    __tablename__ = 'permisos_evaluacion'
    
    id = db.Column(db.Integer, primary_key=True)
    evaluador_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    evaluado_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    evaluador = db.relationship('User', foreign_keys=[evaluador_id], backref=db.backref('permisos_como_evaluador', lazy=True, cascade='all, delete-orphan'))
    evaluado = db.relationship('User', foreign_keys=[evaluado_id], backref=db.backref('permisos_como_evaluado', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('evaluador_id', 'evaluado_id', name='uq_evaluador_evaluado'),)
    
    def __repr__(self):
        return f'<PermisosEvaluacion {self.evaluador_id} -> {self.evaluado_id}>'


class ContactoEmergencia(db.Model):
    __tablename__ = 'contacto_emergencia'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)

    nombre_contacto = db.Column(db.String(120), nullable=False)
    parentesco = db.Column(db.String(50), nullable=False)
    otro_parentesco = db.Column(db.String(50), nullable=True)

    telefono_contacto = db.Column(db.String(15), nullable=False)
    calle_numero = db.Column(db.String(150), nullable=False)
    colonia = db.Column(db.String(150), nullable=False)

    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('contacto_emergencia', uselist=False))
