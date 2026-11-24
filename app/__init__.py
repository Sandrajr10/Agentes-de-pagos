from flask import Flask
import os
from dotenv import load_dotenv

from app.services.formatos import formato_monto


def create_app():
    """Crea y configura la aplicación Flask."""
    load_dotenv()

    app = Flask(__name__)

    # Filtro para mostrar montos con separador de miles y símbolo
    app.jinja_env.filters["formato_monto"] = formato_monto

    # Configuración básica
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["AGENT_API_KEY"] = os.environ.get("AGENT_API_KEY", "")

    # Registro de controladores (blueprints)
    from app.controllers import main_bp
    app.register_blueprint(main_bp)

    return app
