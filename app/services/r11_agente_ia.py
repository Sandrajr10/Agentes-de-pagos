"""Servicios de lógica de negocio - Integración del agente de IA

El agente de IA interpreta la moneda de cada operación y redacta el mensaje
del aviso. Respeta el contrato JSON definido en AGENTS.md.
"""

import os
from dotenv import load_dotenv

load_dotenv()

AGENT_API_KEY = os.environ.get("AGENT_API_KEY", "")


def agente_ia_interpretar(operacion: dict) -> dict:
    """Interpreta la moneda y redacta el mensaje del aviso para una operación.

    Si hay una llave de API del agente configurada en .env, se podría llamar
    a la API externa. Mientras tanto, usa la lógica local para interpretar
    la moneda y redactar el mensaje, respetando el contrato JSON.

    Args:
        operacion: Diccionario con banco, moneda, monto, dias_para_vencer,
                   tipo_alerta, fecha_vencimiento.

    Returns:
        Diccionario con el contrato JSON:
        {
            "banco": texto,
            "moneda": texto,
            "monto": número,
            "mensaje": texto,
            "dias_para_vencer": número,
            "tipo_alerta": texto
        }
    """
    banco = operacion.get("banco", "no indicado")
    moneda = operacion.get("moneda", "no indicado")
    monto = operacion.get("monto", "no indicado")
    dias = operacion.get("dias_para_vencer", "no indicado")
    tipo = operacion.get("tipo_alerta", "no indicado")

    # Redactar mensaje según el tipo de alerta
    if tipo == "semana":
        mensaje = f"La operación del banco {banco} vence esta semana en {dias} días. Moneda: {moneda}. Monto a pagar: {monto}."
    elif tipo == "dia":
        mensaje = f"¡URGENTE! La operación del banco {banco} vence mañana ({dias} día). Moneda: {moneda}. Monto a pagar: {monto}."
    else:
        mensaje = f"Operación del banco {banco}. Moneda: {moneda}. Monto a pagar: {monto}. Días para vencer: {dias}."

    return {
        "banco": banco if banco else "no indicado",
        "moneda": moneda if moneda else "no indicado",
        "monto": monto if monto is not None else "no indicado",
        "mensaje": mensaje,
        "dias_para_vencer": dias if dias is not None else "no indicado",
        "tipo_alerta": tipo if tipo else "no indicado",
    }


def agente_ia_disponible() -> bool:
    """Indica si hay una llave de API del agente configurada en .env."""
    return bool(AGENT_API_KEY and AGENT_API_KEY.strip())
