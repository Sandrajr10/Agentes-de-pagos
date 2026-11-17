from flask import Flask
import os
from dotenv import load_dotenv


def create_app():
    """Crea y configura la aplicación Flask."""
    load_dotenv()

    app = Flask(__name__)

    # Configuración básica
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["AGENT_API_KEY"] = os.environ.get("AGENT_API_KEY", "")

    # Registro de controladores (blueprints)
    from app.controllers import main_bp
    app.register_blueprint(main_bp)

    return app
