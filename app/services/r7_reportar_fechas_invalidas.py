"""Servicios de lógica de negocio - Regla R7

R7: Si `Próximo Pago` es `--/--/----` o está vacío, la fila se reporta como
error y no se procesa.
"""


def reportar_fechas_invalidas(filas: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separa las filas con fecha de vencimiento inválida de las válidas.

    Una fecha es inválida si es "--/--/----", vacía, o no se pudo parsear
    (fecha_vencimiento es None y dias_para_vencer es None).

    Args:
        filas: Lista de diccionarios con dias_para_vencer y fecha_vencimiento.

    Returns:
        Tupla (filas_validas, filas_con_error). Las filas con error tienen
        una clave adicional 'motivo_error' describiendo el problema.
    """
    filas_validas = []
    filas_con_error = []

    for fila in filas:
        # Saltar filas de sección
        if fila.get("es_seccion"):
            continue

        dias = fila.get("dias_para_vencer")
        fecha = fila.get("fecha_vencimiento")

        if dias is None and fecha is None:
            fila_con_error = dict(fila)
            fila_con_error["motivo_error"] = "Fecha de vencimiento inválida o vacía (--/--/----)"
            filas_con_error.append(fila_con_error)
        else:
            filas_validas.append(fila)

    return filas_validas, filas_con_error
