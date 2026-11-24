"""Pruebas del formato de montos y del botón 'Probar correo'."""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app.services.r10_envio_correo as correo
from app import create_app
from app.services.formatos import formato_monto


class SMTPPrueba:
    """Doble de prueba para smtplib.SMTP."""

    error = None
    inicio_sesion = None

    def __init__(self, servidor, puerto, timeout=None):
        self.servidor = servidor
        self.puerto = puerto

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        pass

    def login(self, usuario, contrasena):
        if SMTPPrueba.error:
            raise SMTPPrueba.error
        SMTPPrueba.inicio_sesion = (usuario, contrasena)


OPERACIONES = [
    {
        "banco": "El General30030502",
        "moneda": "dólares",
        "monto": 108410.93,
        "dias_para_vencer": 1,
        "tipo_alerta": "dia",
        "fecha_vencimiento": "19/11/2026",
        "mensaje_ia": "Vence mañana.",
    },
    {
        "banco": "BCR 6181708",
        "moneda": "colones",
        "monto": 68166666.66,
        "dias_para_vencer": 7,
        "tipo_alerta": "semana",
        "fecha_vencimiento": "25/11/2026",
        "mensaje_ia": "Vence esta semana.",
    },
]


@pytest.fixture(autouse=True)
def _limpiar():
    SMTPPrueba.error = None
    SMTPPrueba.inicio_sesion = None
    yield


def _cliente():
    app = create_app()
    app.config["TESTING"] = True
    cliente = app.test_client()
    with cliente.session_transaction() as sesion:
        sesion["usuario_autenticado"] = True
        sesion["operaciones"] = OPERACIONES
        sesion["total_operaciones"] = 25
        sesion["contador_semana"] = 1
        sesion["contador_dia"] = 1
        sesion["contador_errores"] = 0
        sesion["errores"] = []
    return cliente


def _configurar(monkeypatch):
    monkeypatch.setenv("SMTP_SERVIDOR", "smtp.office365.com")
    monkeypatch.setenv("SMTP_PUERTO", "587")
    monkeypatch.setenv("SMTP_USUARIO", "avisos@montecillos.com")
    monkeypatch.setenv("SMTP_CONTRASENA", "clave")
    monkeypatch.setenv("SMTP_TLS", "true")
    monkeypatch.setattr(correo.smtplib, "SMTP", SMTPPrueba)


def test_formato_monto_dolares():
    assert formato_monto(108410.93, "dólares") == "$108,410.93"


def test_formato_monto_colones():
    assert formato_monto(68166666.66, "colones") == "₡68,166,666.66"


def test_formato_monto_sin_dato():
    assert formato_monto(None, "colones") == "no indicado"


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("smtp.office365.com", "smtp.office365.com"),
        ("https://smtp.office365.com", "smtp.office365.com"),
        ("https://smtp.office365.com/", "smtp.office365.com"),
        (" smtp.office365.com ", "smtp.office365.com"),
        ("smtp.office365.com:587", "smtp.office365.com"),
        ('"smtp.office365.com"', "smtp.office365.com"),
        ("SMTP.Office365.com", "smtp.office365.com"),
        ("servidor smtp.office365.com", "smtp.office365.com"),
        ("SMTP_SERVIDOR=smtp.office365.com", "smtp.office365.com"),
        ("servidor: smtp.office365.com:587", "smtp.office365.com"),
        ("smtp.office365.com puerto 587", "smtp.office365.com"),
    ],
)
def test_limpiar_servidor(valor, esperado):
    assert correo.limpiar_servidor(valor) == esperado


def test_pantalla_muestra_montos_formateados():
    cliente = _cliente()
    html = cliente.get("/resultados").get_data(as_text=True)

    assert "$108,410.93" in html
    assert "₡68,166,666.66" in html


def test_probar_correo_correcto(monkeypatch):
    _configurar(monkeypatch)

    respuesta = _cliente().post("/probar-correo", follow_redirects=True)
    html = respuesta.get_data(as_text=True)

    assert "Conexión de correo correcta" in html
    assert SMTPPrueba.inicio_sesion == ("avisos@montecillos.com", "clave")


def test_probar_correo_con_servidor_inexistente(monkeypatch):
    import socket

    _configurar(monkeypatch)
    SMTPPrueba.error = socket.gaierror(-2, "Name or service not known")

    respuesta = _cliente().post("/probar-correo", follow_redirects=True)
    html = respuesta.get_data(as_text=True)

    assert "Falló la prueba de correo" in html
    assert "SMTP_SERVIDOR" in html
