from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_restful import Api
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'

    api = Api(app)
    print("API initialized:", api)

    with app.app_context():
        from . import models
        from .routes import routes_bp
        app.register_blueprint(routes_bp)
        db.create_all()
        from .api import register_resources
        print("Registering resources...")
        register_resources(api)
        print("Resources registered.")

        print("Registered routes:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint}: {rule.rule}")

    return app