"""Pruebas del envío de avisos por correo (R10).

No se conecta a ningún servidor real: se reemplaza smtplib.SMTP por un doble
de prueba que guarda los mensajes enviados.
"""

import sys
import os
import re

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app.services.r10_envio_correo as correo
from app import create_app

DESTINATARIO = "sandra.jimenez@montecillos.com"

OPERACIONES = [
    {
        "banco": "BCR 6181708",
        "moneda": "colones",
        "monto": 68166666.66,
        "dias_para_vencer": 1,
        "tipo_alerta": "dia",
        "fecha_vencimiento": "19/11/2026",
        "mensaje_ia": "La operación vence mañana.",
    },
    {
        "banco": "BAC SAN JOSE 95894",
        "moneda": "dólares",
        "monto": 52686997.0,
        "dias_para_vencer": 7,
        "tipo_alerta": "semana",
        "fecha_vencimiento": "25/11/2026",
        "mensaje_ia": "La operación vence esta semana.",
    },
]


class SMTPFalso:
    """Doble de prueba para smtplib.SMTP."""

    mensajes = []
    inicios_sesion = []
    servidores = []
    error_al_enviar = None

    def __init__(self, servidor, puerto, timeout=None):
        self.servidor = servidor
        self.puerto = puerto
        SMTPFalso.servidores.append((servidor, puerto))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        self.tls = True

    def login(self, usuario, contrasena):
        SMTPFalso.inicios_sesion.append((usuario, contrasena))

    def send_message(self, mensaje):
        if SMTPFalso.error_al_enviar:
            raise SMTPFalso.error_al_enviar
        SMTPFalso.mensajes.append(mensaje)


@pytest.fixture(autouse=True)
def _limpiar_doble():
    """Deja el doble de prueba en cero antes de cada prueba."""
    SMTPFalso.mensajes = []
    SMTPFalso.inicios_sesion = []
    SMTPFalso.servidores = []
    SMTPFalso.error_al_enviar = None
    yield


def _configurar_entorno(monkeypatch):
    monkeypatch.setenv("SMTP_SERVIDOR", "smtp.ejemplo.com")
    monkeypatch.setenv("SMTP_PUERTO", "587")
    monkeypatch.setenv("SMTP_USUARIO", "avisos@montecillos.com")
    monkeypatch.setenv("SMTP_CONTRASENA", "clave-smtp")
    monkeypatch.setenv("SMTP_TLS", "true")


def _cliente_con_operaciones():
    app = create_app()
    app.config["TESTING"] = True
    cliente = app.test_client()
    with cliente.session_transaction() as sesion:
        sesion["usuario_autenticado"] = True
        sesion["operaciones"] = OPERACIONES
    return cliente


def test_envia_un_correo_por_operacion(monkeypatch):
    """R10: se envía un correo por cada operación detectada al jefe."""
    _configurar_entorno(monkeypatch)
    monkeypatch.setattr(correo.smtplib, "SMTP", SMTPFalso)

    for operacion in OPERACIONES:
        correo.enviar_aviso_operacion(operacion)

    assert len(SMTPFalso.mensajes) == 2
    asuntos = [m["Subject"] for m in SMTPFalso.mensajes]
    assert any("BCR 6181708" in a for a in asuntos)
    assert all(m["To"] == DESTINATARIO for m in SMTPFalso.mensajes)
    assert SMTPFalso.inicios_sesion[0] == ("avisos@montecillos.com", "clave-smtp")


def test_cuerpo_del_correo_trae_banco_moneda_y_monto(monkeypatch):
    """El aviso indica banco, moneda y monto a pagar."""
    _configurar_entorno(monkeypatch)
    monkeypatch.setattr(correo.smtplib, "SMTP", SMTPFalso)

    correo.enviar_aviso_operacion(OPERACIONES[1])
    cuerpo = SMTPFalso.mensajes[0].get_content()

    assert "BAC SAN JOSE 95894" in cuerpo
    assert "dólares" in cuerpo
    assert "52,686,997.00" in cuerpo
    assert "25/11/2026" in cuerpo


def test_registra_envio_con_fecha_y_destinatario(monkeypatch, tmp_path):
    """R10: el registro guarda fecha, hora y destinatario."""
    ruta = tmp_path / "envios.log"
    monkeypatch.setenv("REGISTRO_ENVIOS", str(ruta))

    correo.registrar_envio(DESTINATARIO, "BCR 6181708", "dia", True)

    contenido = ruta.read_text(encoding="utf-8")
    assert DESTINATARIO in contenido
    assert "ENVIADO" in contenido
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", contenido)


def test_ruta_envia_todos_los_avisos(monkeypatch, tmp_path):
    """El botón envía un correo por operación y lo anota en el registro."""
    _configurar_entorno(monkeypatch)
    monkeypatch.setattr(correo.smtplib, "SMTP", SMTPFalso)
    ruta = tmp_path / "envios.log"
    monkeypatch.setenv("REGISTRO_ENVIOS", str(ruta))

    cliente = _cliente_con_operaciones()
    respuesta = cliente.post("/enviar-aviso", follow_redirects=True)
    html = respuesta.get_data(as_text=True)

    assert "Se enviaron 2 aviso(s)" in html
    assert len(SMTPFalso.mensajes) == 2
    assert len(ruta.read_text(encoding="utf-8").strip().splitlines()) == 2


def test_ruta_avisa_si_falta_configuracion(monkeypatch, tmp_path):
    """Sin variables SMTP se avisa en pantalla y no se intenta enviar."""
    for variable in ("SMTP_SERVIDOR", "SMTP_USUARIO", "SMTP_CONTRASENA"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(correo.smtplib, "SMTP", SMTPFalso)
    monkeypatch.setenv("REGISTRO_ENVIOS", str(tmp_path / "envios.log"))

    cliente = _cliente_con_operaciones()
    respuesta = cliente.post("/enviar-aviso", follow_redirects=True)
    html = respuesta.get_data(as_text=True)

    assert "El correo no está configurado" in html
    assert SMTPFalso.mensajes == []


def test_ruta_informa_fallos_de_envio(monkeypatch, tmp_path):
    """Si el servidor rechaza el correo, se avisa y se registra el error."""
    _configurar_entorno(monkeypatch)
    monkeypatch.setattr(correo.smtplib, "SMTP", SMTPFalso)
    monkeypatch.setattr(SMTPFalso, "error_al_enviar", OSError("sin conexión"))
    monkeypatch.setenv("REGISTRO_ENVIOS", str(tmp_path / "envios.log"))

    cliente = _cliente_con_operaciones()
    respuesta = cliente.post("/enviar-aviso", follow_redirects=True)
    html = respuesta.get_data(as_text=True)

    assert "fallaron" in html
    assert "ERROR" in (tmp_path / "envios.log").read_text(encoding="utf-8")
