from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import os
from datetime import timedelta

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()  # 🔹 Agregamos Flask-Mail

def create_app():
    app = Flask(__name__)
    
    # 🔹 Configuración general
    app.config['SECRET_KEY'] = 'clave_secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///intranet.db'
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    app.config['SESSION_PROTECTION'] = "strong"

    # 🔹 Configuración de Flask-Mail
    app.config['MAIL_SERVER'] = 'bomberosdeleon.org'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'cristian.rodriguez@bomberosdeleon.org'
    app.config['MAIL_PASSWORD'] = 'n4h2y4F2^'
    app.config['MAIL_DEFAULT_SENDER'] = 'soporte@bomberosdeleon.org'

    # 🔹 Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)  # 🔹 Inicializamos Flask-Mail correctamente

    login_manager.login_view = "main.login"
    login_manager.login_message_category = "warning"

    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        from app.models import User
        db.create_all()

    # 🔹 Mover `user_loader` dentro de `create_app()`
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app


