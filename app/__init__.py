from flask import Flask, request, current_app
from config import Config
from sqlalchemy import MetaData
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging, os
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

bootstrap = Bootstrap5()
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)
migrate = Migrate()
login = LoginManager()
apscheduler = BackgroundScheduler()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    bootstrap.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    login.init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.dash import bp as dash_bp
    app.register_blueprint(dash_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app import audit
    audit.register_audit_listeners()

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/alveusclips.log', maxBytes=100000, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('AlveusClips startup')

    return app

from app import models