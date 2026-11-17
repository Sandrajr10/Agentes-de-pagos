import os
import sys

# Asegurar que la raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app import create_app


@pytest.fixture
def app():
    """Crea la aplicación Flask en modo testing."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    yield app


@pytest.fixture
def client(app):
    """Cliente de prueba para hacer peticiones HTTP."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Corredor de comandos CLI."""
    return app.test_cli_runner()


def test_app_esta_viva(client):
    """Prueba que la aplicación responde en la ruta principal."""
    respuesta = client.get("/")
    assert respuesta.status_code == 200
