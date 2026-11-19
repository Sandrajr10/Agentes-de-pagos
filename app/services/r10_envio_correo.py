"""Servicios de lógica de negocio - Regla R10

R10: El destinatario de los avisos es sandra.jimenez@montecillos.com.
"""

import os
from dotenv import load_dotenv

load_dotenv()

DESTINATARIO_JEFE = "sandra.jimenez@montecillos.com"


def obtener_configuracion_correo() -> dict:
    """Obtiene la configuración SMTP desde variables de entorno (.env).

    Returns:
        Diccionario con servidor, puerto, usuario, contraseña y uso_tls.
        Retorna valores vacíos si no están configurados.
    """
    return {
        "servidor": os.environ.get("SMTP_SERVIDOR", ""),
        "puerto": int(os.environ.get("SMTP_PUERTO", "587")),
        "usuario": os.environ.get("SMTP_USUARIO", ""),
        "contraseña": os.environ.get("SMTP_CONTRASENA", ""),
        "usar_tls": os.environ.get("SMTP_TLS", "true").lower() == "true",
        "destinatario": DESTINATARIO_JEFE,
    }


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
        banco = op.get("banco", "no indicado")
        moneda = op.get("moneda", "no indicado")
        monto = op.get("monto", "no indicado")
        dias = op.get("dias_para_vencer", "no indicado")
        tipo = op.get("tipo_alerta", "")

        if tipo == "semana":
            alerta = "ESTA SEMANA"
        else:
            alerta = "VENCE MAÑANA"

        lineas.append(
            f"- {alerta}: {banco} | {moneda} | Monto: {monto} | Días: {dias}"
        )

    lineas.append(f"\nDestinatario: {DESTINATARIO_JEFE}")
    return "\n".join(lineas)
