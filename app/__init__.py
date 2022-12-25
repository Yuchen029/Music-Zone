from flask import Flask, render_template
from config import config
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_babel import Babel

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins='*')
login_manager.login_view = 'auth.login'
babel = Babel()


def create_app(cfg_type: str):
    """
    Do initlization for flask application

    :param cfg_type: a string with content ('dev', 'test', 'release')
    :return: app: flask application to run
    """
    app = Flask(__name__)
    app.config.from_object(config[cfg_type])
    config[cfg_type].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    babel.init_app(app)



    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .chat import chat as chat_blueprint
    app.register_blueprint(chat_blueprint)

    from .live import live as live_blueprint
    app.register_blueprint(live_blueprint)

    return app

