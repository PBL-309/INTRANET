import os
import site
import sys
import tempfile
import types
import unittest
import datetime
from decimal import Decimal

site.addsitedir(os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages'))

# La copia local del entorno no contiene Flask-Mail; el módulo no participa en estas pruebas.
if 'flask_mail' not in sys.modules:
    flask_mail = types.ModuleType('flask_mail')
    class Mail:
        def init_app(self, app):
            return None
        def send(self, message):
            return None
    class Message:
        def __init__(self, *args, **kwargs):
            pass
    flask_mail.Mail = Mail
    flask_mail.Message = Message
    sys.modules['flask_mail'] = flask_mail
if 'requests' not in sys.modules:
    requests = types.ModuleType('requests')
    requests.get = lambda *args, **kwargs: None
    requests.post = lambda *args, **kwargs: None
    sys.modules['requests'] = requests

db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
db_file.close()
os.environ['INTRANET_DATABASE_URI'] = 'sqlite:///' + db_file.name.replace('\\', '/')

from flask import Flask
from app import db
from app.models import AreaCompra, OrdenCompra, PartidaOrdenCompra, User


class OrdenesCompraTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI=os.environ['INTRANET_DATABASE_URI'],
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(cls.app)
        with cls.app.app_context():
            db.create_all()
            user = User(username='capturista', nombre='Usuario Prueba')
            user.set_password('temporal')
            db.session.add(user)
            db.session.commit()
            cls.user_id = user.id

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        os.unlink(db_file.name)

    def test_crea_orden_y_avanza_consecutivo_del_area(self):
        with self.app.app_context():
            area = AreaCompra(nombre='SOPORTE TÉCNICO', codigo='SP', ultimo_consecutivo=80)
            db.session.add(area)
            db.session.flush()
            consecutivo, codigo = db.session.execute(
                db.text('UPDATE area_compra SET ultimo_consecutivo=ultimo_consecutivo+1 WHERE id=:id RETURNING ultimo_consecutivo,codigo'),
                {'id': area.id},
            ).one()
            orden = OrdenCompra(
                area_id=area.id, consecutivo=consecutivo, folio=f'PBL/{codigo}/{consecutivo:03d}',
                solicitante_id=self.user_id, fecha=datetime.date(2026, 9, 1), proveedor='Proveedor Demo',
                cuenta_presupuestal='3811', justificacion='Prueba', iva_porcentaje=Decimal('16'),
            )
            orden.partidas.append(PartidaOrdenCompra(posicion=1, cantidad=Decimal('2'), descripcion='Artículo', precio_unitario=Decimal('100.50')))
            db.session.add(orden)
            db.session.commit()
            orden = OrdenCompra.query.one()
            self.assertEqual(orden.folio, 'PBL/SP/081')
            self.assertEqual(orden.total.quantize(Decimal('0.01')), Decimal('233.16'))


if __name__ == '__main__':
    unittest.main()
