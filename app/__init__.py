import random
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
from datetime import timedelta
from dotenv import load_dotenv

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
apscheduler = BackgroundScheduler(timezone="UTC")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

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

    @app.context_processor
    def inject_logo():
        static_path = os.path.join(app.root_path, 'static')
        clip_png_files = [f for f in os.listdir(static_path) if f.lower().endswith('.png') and 'clip' in f.lower()] if os.path.exists(static_path) else []

        load_dotenv(override=True)
        LOGO_FILENAME = os.environ.get('LOGO_FILENAME', 'random')

        if (LOGO_FILENAME == 'random' or LOGO_FILENAME == '') and clip_png_files:
            LOGO_FILENAME = random.choice(clip_png_files)

        return dict(LOGO_FILENAME=LOGO_FILENAME)

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/cliprepo.log', maxBytes=100000, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('ClipRepo startup')

    return app

from app import models