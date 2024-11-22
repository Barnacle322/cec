import locale
import os
from datetime import timedelta

from flask import Flask, session
from werkzeug.middleware.proxy_fix import ProxyFix

from .admin import admin
from .extenstions import babel, db, login_manager, migrate
from .main import main


def create_app(database_url="sqlite:///db.sqlite"):
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("_DATABASE_URL", database_url)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
    app.config["SQLALCHEMY_RECORD_QUERIES"] = True
    app.config["SQLALCHEMY_POOL_SIZE"] = int(os.getenv("SQLALCHEMY_POOL_SIZE", 5))
    app.config["SQLALCHEMY_POOL_RECYCLE"] = int(
        os.getenv("SQLALCHEMY_POOL_RECYCLE", 1800)
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"

    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=30)
    # app.config["SQLALCHEMY_ECHO"] = True
    app.secret_key = os.getenv("SECRET_KEY", "18c2ff95-83a1-4998-8bee-0c6a2170497c")

    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix="/admin")

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    def get_locale():
        return session.get("lang", "ru")

    babel.init_app(
        app,
        locale_selector=get_locale,
    )

    @app.before_request
    def set_locale():
        user_locale = get_locale()
        if user_locale == "ru":
            locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
        else:
            locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

    # Reverse proxy support
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    return app


application = create_app()
