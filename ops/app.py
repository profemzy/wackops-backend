from celery import Celery
from celery import Task
from flask import Flask
from flask import jsonify
from werkzeug.debug import DebuggedApplication
from werkzeug.middleware.proxy_fix import ProxyFix

from ops.api.v1 import api_v1
from ops.extensions import db
from ops.extensions import debug_toolbar
from ops.extensions import flask_static_digest
from ops.extensions import jwt
from ops.extensions import swagger
from ops.page.views import page
from ops.up.views import up
from ops.user.models import User


def create_celery_app(app=None):
    """
    Create a new Celery app and tie together the Celery config to the app's
    config. Wrap all tasks in the context of the application.

    :param app: Flask app
    :return: Celery app
    """
    app = app or create_app()

    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(app.import_name, task_cls=FlaskTask)
    celery.conf.update(app.config.get("CELERY_CONFIG", {}))
    celery.set_default()
    app.extensions["celery"] = celery

    return celery


def create_app(settings_override=None):
    """
    Create a Flask application using the app factory pattern.

    :param settings_override: Override settings
    :return: Flask app
    """
    app = Flask(__name__, static_folder="../public", static_url_path="")

    app.config.from_object("config.settings")

    if settings_override:
        app.config.update(settings_override)

    middleware(app)

    app.register_blueprint(up)
    app.register_blueprint(page)
    app.register_blueprint(api_v1)

    extensions(app)
    jwt_callbacks()

    return app


def extensions(app):
    """
    Register 0 or more extensions (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    debug_toolbar.init_app(app)
    jwt.init_app(app)
    db.init_app(app)
    swagger.init_app(app)
    flask_static_digest.init_app(app)


    return None


def jwt_callbacks():
    """
    Set up custom behavior for JWT based authentication.

    :return: None
    """

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.filter((User.username == identity)).first()

    @jwt.unauthorized_loader
    def unauthorized_callback(_jwt_payload):
        response = {
            "error": {"message": "Your auth token or CSRF token are missing"}
        }

        return jsonify(response), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_headers, jwt_payload):
        response = {"error": {"message": "Your auth token has expired"}}

        return jsonify(response), 401

    return None


def middleware(app):
    """
    Register 0 or more middleware (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    # Enable the Flask interactive debugger in the browser for development.
    if app.debug:
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    # Set the real IP address into request.remote_addr when behind a proxy.
    app.wsgi_app = ProxyFix(app.wsgi_app)

    return None


celery_app = create_celery_app()
