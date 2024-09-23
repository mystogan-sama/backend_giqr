import threading

from flask import Flask
from config import config_by_name
from .extensions import bcrypt, cors, db, jwt, ma
from .sso_helper import syncronize_resource, domain_claims
from .task.bridge import internalApi_byUrl


def before_run_app():
    domain_claims()
    threading.Thread(target=internalApi_byUrl,
                     args=({"url": "sync_resource"}, 'http://127.0.0.1:5000')).start()


def create_app(config_name):
    before_run_app()
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    register_extensions(app)
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix="")
    from .task import internal_bp
    app.register_blueprint(internal_bp, url_prefix="/internal")
    return app


def register_extensions(app):
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)