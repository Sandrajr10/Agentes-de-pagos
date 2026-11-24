"""Servicios de lógica de negocio - Regla R10

R10: El destinatario de los avisos es sandra.jimenez@montecillos.com.

El aviso se envía por SMTP con la configuración guardada en variables de
entorno (.env en local, variables de entorno en el servidor).
"""

import os
import smtplib
import socket
import tempfile
from email.message import EmailMessage

from dotenv import load_dotenv

from app.services.formatos import formato_monto
from app.services.tiempo import ZONA_COSTA_RICA
from datetime import datetime

load_dotenv()

DESTINATARIO_JEFE = "sandra.jimenez@montecillos.com"


def limpiar_servidor(valor: str) -> str:
    """Deja solo el nombre del servidor SMTP.

    Acepta valores escritos como dirección web o con texto de más y quita
    espacios, comillas, el nombre de la variable, el protocolo (https://), la
    ruta y el puerto. Así "https://smtp.office365.com/" o
    "servidor smtp.office365.com" se convierten en "smtp.office365.com".
    """
    servidor = (valor or "").strip().strip("\"'").strip()
    if "=" in servidor:
        servidor = servidor.split("=", 1)[1]
    if "://" in servidor:
        servidor = servidor.split("://", 1)[1]
    servidor = servidor.split("/", 1)[0].strip()

    # Si quedó texto adicional, se toma la palabra que parece un servidor
    # (tiene punto y no tiene espacios).
    candidatos = [parte for parte in servidor.split() if "." in parte]
    if candidatos:
        servidor = candidatos[-1]

    servidor = servidor.strip("\"'()").strip()
    if servidor.count(":") == 1:
        host, posible_puerto = servidor.rsplit(":", 1)
        if posible_puerto.isdigit():
            servidor = host
    return servidor.strip().strip(".").lower()


def obtener_configuracion_correo() -> dict:
    """Obtiene la configuración SMTP desde variables de entorno (.env).

    Returns:
        Diccionario con servidor, puerto, usuario, contraseña y uso_tls.
        Retorna valores vacíos si no están configurados.
    """
    puerto = os.environ.get("SMTP_PUERTO", "587").strip()
    try:
        puerto = int(puerto)
    except ValueError:
        puerto = 587

    return {
        "servidor": limpiar_servidor(os.environ.get("SMTP_SERVIDOR", "")),
        "puerto": puerto,
        "usuario": os.environ.get("SMTP_USUARIO", "").strip(),
        "contrasena": os.environ.get("SMTP_CONTRASENA", "").strip(),
        "usar_tls": os.environ.get("SMTP_TLS", "true").strip().lower() != "false",
        "destinatario": DESTINATARIO_JEFE,
    }


def correo_configurado() -> bool:
    """Indica si están definidos el servidor, el usuario y la contraseña."""
    config = obtener_configuracion_correo()
    return bool(config["servidor"] and config["usuario"] and config["contrasena"])


def probar_conexion_correo(config: dict | None = None) -> None:
    """Prueba la conexión con el servidor de correo sin enviar ningún mensaje.

    Se conecta, inicia TLS si está configurado y valida el usuario y la
    contraseña. Lanza una excepción con el problema encontrado.
    """
    config = config or obtener_configuracion_correo()
    if not (config["servidor"] and config["usuario"]):
        raise RuntimeError("La configuración de correo está incompleta.")

    with smtplib.SMTP(config["servidor"], config["puerto"], timeout=20) as servidor:
        if config["usar_tls"]:
            servidor.starttls()
        if config["contrasena"]:
            servidor.login(config["usuario"], config["contrasena"])


def preparar_aviso(operaciones: list[dict]) -> str:
    """Prepara el contenido del mensaje de aviso para el jefe.

    Args:
        operaciones: Lista de operaciones por vencer con banco, moneda, monto,
                     dias_para_vencer y tipo_alerta.

    Returns:
        Texto del mensaje del correo.
    """
    if not operaciones:
        return "Sin vencimientos programados para mañana ni para la semana en curso."

    lineas = ["Avisos de vencimiento de operaciones bancarias:\n"]
    for op in operaciones:
        alerta = _texto_alerta(op)
        lineas.append(
            f"- {alerta}: {op.get('banco', 'no indicado')} | {op.get('moneda', 'no indicado')} "
            f"| Monto: {_formatear_monto(op)} | Días: {op.get('dias_para_vencer', 'no indicado')}"
        )

    lineas.append(f"\nDestinatario: {DESTINATARIO_JEFE}")
    return "\n".join(lineas)


def _texto_alerta(operacion: dict) -> str:
    """Texto de la alerta según los días que faltan."""
    if operacion.get("tipo_alerta") == "semana":
        return "ESTA SEMANA"
    return "VENCE MAÑANA"


def _formatear_monto(operacion: dict) -> str:
    """Devuelve el monto con separador de miles y su símbolo."""
    return formato_monto(operacion.get("monto"), operacion.get("moneda"))


def _cuerpo_operacion(operacion: dict) -> str:
    """Redacta el cuerpo del correo de una operación."""
    banco = operacion.get("banco") or "no indicado"
    moneda = operacion.get("moneda") or "no indicado"
    dias = operacion.get("dias_para_vencer", "no indicado")
    fecha = operacion.get("fecha_vencimiento") or "no indicado"
    alerta = _texto_alerta(operacion)

    return (
        f"Aviso de vencimiento bancario\n\n"
        f"Alerta: {alerta}\n"
        f"Banco: {banco}\n"
        f"Moneda: {moneda}\n"
        f"Monto a pagar: {_formatear_monto(operacion)}\n"
        f"Fecha de vencimiento: {fecha}\n"
        f"Días para vencer: {dias}\n\n"
        f"{operacion.get('mensaje_ia', '')}\n\n"
        "Este aviso lo genera la aplicación de control de pagos. "
        "La decisión de ejecutar el pago corresponde al jefe.\n"
    )


def enviar_aviso_operacion(operacion: dict, config: dict | None = None) -> None:
    """Envía un correo de aviso por una operación al jefe.

    Lanza una excepción si el correo no se puede enviar, para que el
    controlador registre el error.

    Args:
        operacion: Diccionario con banco, moneda, monto, dias_para_vencer,
                   tipo_alerta y fecha_vencimiento.
        config: Configuración SMTP opcional (por defecto se lee del entorno).
    """
    config = config or obtener_configuracion_correo()
    if not (config["servidor"] and config["usuario"]):
        raise RuntimeError("La configuración de correo está incompleta.")

    mensaje = EmailMessage()
    mensaje["Subject"] = (
        f"Aviso de vencimiento bancario - {operacion.get('banco', 'no indicado')} - "
        f"{_texto_alerta(operacion).lower()}"
    )
    mensaje["From"] = config["usuario"]
    mensaje["To"] = config["destinatario"]
    mensaje.set_content(_cuerpo_operacion(operacion))

    with smtplib.SMTP(config["servidor"], config["puerto"], timeout=30) as servidor:
        if config["usar_tls"]:
            servidor.starttls()
        if config["contrasena"]:
            servidor.login(config["usuario"], config["contrasena"])
        servidor.send_message(mensaje)


def describir_error(error: Exception) -> str:
    """Traduce los errores de correo más comunes a un mensaje entendible."""
    texto = str(error)
    if isinstance(error, socket.gaierror) or "Name or service not known" in texto:
        return (
            "no se encontró el servidor de correo. Revise la variable "
            "SMTP_SERVIDOR (por ejemplo smtp.office365.com)."
        )
    if isinstance(error, smtplib.SMTPAuthenticationError):
        return (
            "el servidor rechazó el usuario o la contraseña. Revise "
            "SMTP_USUARIO y SMTP_CONTRASENA."
        )
    if isinstance(error, (smtplib.SMTPConnectError, ConnectionRefusedError)) or "Connection refused" in texto:
        return (
            "no se pudo conectar al servidor de correo. Revise SMTP_SERVIDOR "
            "y SMTP_PUERTO."
        )
    if isinstance(error, (TimeoutError, socket.timeout)) or "timed out" in texto.lower():
        return (
            "el servidor de correo no respondió a tiempo. Revise SMTP_PUERTO "
            "(587) o si su proveedor bloquea la conexión."
        )
    return texto[:200]


def _rutas_registro() -> list[str]:
    """Rutas donde se intenta guardar el registro, en orden de preferencia.

    La primera es la configurada con REGISTRO_ENVIOS (por ejemplo el disco de
    Render montado en /var/data). Si no se puede escribir, se usa la carpeta
    del proyecto y, de último, la carpeta temporal del sistema.
    """
    principal = os.environ.get("REGISTRO_ENVIOS", "").strip()
    rutas = [principal] if principal else []
    rutas.append(os.path.join("registros", "envios.log"))
    rutas.append(os.path.join(tempfile.gettempdir(), "envios.log"))
    return rutas


def registrar_envio(destinatario: str, banco: str, tipo_alerta: str, exito: bool, detalle: str = "") -> None:
    """Anota el envío en el archivo de registro con fecha y hora.

    El archivo se define con la variable REGISTRO_ENVIOS y por defecto es
    registros/envios.log. Además siempre se escribe en la salida del servidor
    para que quede en los Logs de Render.
    """
    ahora = datetime.now(ZONA_COSTA_RICA) if ZONA_COSTA_RICA else datetime.now()
    estado = "ENVIADO" if exito else "ERROR"
    detalle = f" | {detalle}" if detalle else ""
    linea = (
        f"{ahora:%Y-%m-%d %H:%M:%S} | {estado} | {destinatario} | "
        f"{banco or 'no indicado'} | {tipo_alerta or 'no indicado'}{detalle}"
    )

    for ruta in _rutas_registro():
        try:
            carpeta = os.path.dirname(ruta)
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            with open(ruta, "a", encoding="utf-8") as archivo:
                archivo.write(linea + "\n")
            break
        except OSError as e:
            print(f"[registro] No se pudo escribir en '{ruta}': {e}", flush=True)

    print(f"[correo] {linea}", flush=True)
