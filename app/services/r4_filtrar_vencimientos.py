"""Servicios de lógica de negocio - Reglas R4 y R9

R4: Marca para aviso solo las operaciones que faltan exactamente 7 días o
exactamente 1 día para vencer.

R9: No se envían avisos para operaciones que ya vencieron o que vencen en
más de 7 días.
"""


def filtrar_operaciones_por_vencer(filas: list[dict]) -> list[dict]:
    """Filtra las operaciones que deben tener aviso.

    Solo se mantienen las operaciones con dias_para_vencer igual a 7 o 1.
    Las operaciones ya vencidas (dias < 0) o con más de 7 días (dias > 7)
    se omiten. Las filas con dias_para_vencer None (fecha inválida) se
    dejan para que R7 las maneje como error.

    Args:
        filas: Lista de diccionarios con dias_para_vencer calculado.

    Returns:
        Lista de diccionarios solo con operaciones a 7 días o 1 día.
    """
    resultado = []

    for fila in filas:
        dias = fila.get("dias_para_vencer")

        # Si es None, la fecha es inválida o no se pudo parsear (R7 lo maneja)
        if dias is None:
            continue

        # Solo avisar si faltan exactamente 7 días o exactamente 1 día
        if dias in (7, 1):
            fila_nueva = dict(fila)
            if dias == 7:
                fila_nueva["tipo_alerta"] = "semana"
            else:
                fila_nueva["tipo_alerta"] = "dia"
            resultado.append(fila_nueva)

    return resultado
