from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
import os
from datetime import timedelta
import logging
import threading
import re

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()  
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'clave_secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///intranet.db'
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    app.config['SESSION_PROTECTION'] = "strong"
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'sgcpbl@gmail.com'  # tu cuenta de Gmail
    app.config['MAIL_PASSWORD'] = 'xayh sphs fbbd agbt'  # contraseña de aplicación
    app.config['MAIL_DEFAULT_SENDER'] = 'sgcpbl@gmail.com'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

    # Configuración de Google reCAPTCHA v2
    # Claves de producción proporcionadas por el usuario
    app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lf1UmgsAAAAADkKsBHsHZht0D45KBQgo18JOBox'
    app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lf1UmgsAAAAAGkckMYzC2hj_SPzMrDNEBOhguH4'

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)  
    csrf.init_app(app)

    login_manager.login_view = "main.login"
    login_manager.login_message_category = "warning"
    from app.routes import main
    app.register_blueprint(main)

    @app.after_request
    def aplicar_navegacion_global(response):
        """Mantiene toda la intranet en una pestaña y agrega regreso al inicio."""
        if response.is_streamed or response.direct_passthrough or response.mimetype != 'text/html':
            return response

        html = response.get_data(as_text=True)
        if not html:
            return response

        # Quitar aperturas en pestaña nueva declaradas directamente en HTML.
        html = re.sub(
            r'\s+target=(["\'])_blank\1',
            '',
            html,
            flags=re.IGNORECASE,
        )

        navigation_script = """
        <script id="intranet-single-tab-navigation">
        (() => {
            const keepSameTab = (root = document) => {
                root.querySelectorAll?.('a[target="_blank"]').forEach(link => {
                    link.removeAttribute('target');
                });
            };
            keepSameTab();
            new MutationObserver(mutations => mutations.forEach(mutation =>
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        if (node.matches?.('a[target="_blank"]')) node.removeAttribute('target');
                        keepSameTab(node);
                    }
                })
            )).observe(document.documentElement, {childList: true, subtree: true});
            document.addEventListener('click', event => {
                const link = event.target.closest?.('a');
                if (link?.target === '_blank') link.removeAttribute('target');
            }, true);
        })();
        </script>
        """

        home_button = ''
        if current_user.is_authenticated and request.endpoint != 'main.dashboard':
            home_button = """
            <style id="intranet-home-button-style">
            .intranet-home-button{position:fixed;left:18px;bottom:18px;z-index:99999;
                display:inline-flex;align-items:center;gap:8px;padding:10px 14px;
                border-radius:999px;background:#17324d;color:#fff!important;
                text-decoration:none!important;font:700 13px/1.2 'Segoe UI',Arial,sans-serif;
                border:1px solid rgba(255,255,255,.25);box-shadow:0 8px 24px rgba(15,35,55,.24)}
            .intranet-home-button:hover{background:#0f2539;transform:translateY(-1px)}
            @media(max-width:600px){.intranet-home-button{left:12px;bottom:12px;padding:9px 12px}}
            @media print{.intranet-home-button{display:none!important}}
            </style>
            <a class="intranet-home-button" href="/dashboard" aria-label="Volver al inicio">← Volver al inicio</a>
            """

        injection = home_button + navigation_script
        if re.search(r'</body\s*>', html, flags=re.IGNORECASE):
            html = re.sub(r'</body\s*>', injection + '</body>', html, count=1, flags=re.IGNORECASE)
        else:
            html += injection
        response.set_data(html)
        return response

    with app.app_context():
        from app.models import User
        db.create_all()
        
        # Inicializar servicio de reconocimiento facial (DESHABILITADO - Usuario quitó facial recognition)
        # try:
        #     from app.facial_service import init_facial_service, facial_service
        #     if init_facial_service(app):
        #         logging.info("[Facial] Servicio de reconocimiento facial inicializado")
        #         
        #         # Precalcular descriptores en background (no bloquea el servidor)
        #         def precalculate_descriptors_background():
        #             try:
        #                 with app.app_context():
        #                     usuarios = User.query.filter(
        #                         User.foto_url != None,
        #                         User.foto_url != ''
        #                     ).all()
        #                     
        #                     if usuarios:
        #                         usuarios_fotos = [
        #                             {
        #                                 'username': u.username,
        #                                 'nombre': u.nombre,
        #                                 'foto_url': u.foto_url
        #                             }
        #                             for u in usuarios
        #                         ]
        #                         
        #                         result = facial_service.precompute_descriptors(usuarios_fotos)
        #                         logging.info(f"[Facial] Precálculo completado en background: {result} descriptores")
        #             except Exception as e:
        #                 logging.error(f"[Facial] Error en precálculo background: {e}")
        #         
        #         # Lanzar precálculo en thread separado si caché está vacío
        #         if not facial_service.face_descriptors:
        #             logging.info("[Facial] Iniciando precálculo en background...")
        #             bg_thread = threading.Thread(target=precalculate_descriptors_background, daemon=True)
        #             bg_thread.start()
        #         else:
        #             logging.info(f"[Facial] Caché cargado: {len(facial_service.face_descriptors)} descriptores listos")
        #             
        # except ImportError:
        #     logging.warning("[Facial] Servicio facial no disponible (librerías no instaladas)")
        # except Exception as e:
        #     logging.error(f"[Facial] Error inicializando servicio facial: {e}")
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    return app

