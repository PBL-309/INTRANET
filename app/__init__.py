from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
import os
from datetime import timedelta

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
    with app.app_context():
        from app.models import User
        db.create_all()
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    return app


