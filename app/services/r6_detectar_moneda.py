"""Servicios de lógica de negocio - Regla R6

R6: Detecta la moneda por el símbolo de `Saldo Actual`: símbolo "$" indica
dólares; sin símbolo "$" indica colones.
"""


def detectar_moneda(filas: list[dict]) -> list[dict]:
    """Detecta la moneda de cada operación basándose en el símbolo de Saldo Actual.

    Si el valor contiene el símbolo "$", la moneda es "dólares".
    Si no contiene "$", la moneda es "colones".

    Args:
        filas: Lista de diccionarios con las filas de operación (con monto extraído).

    Returns:
        Lista de diccionarios con clave adicional 'moneda' ("dólares" o "colones").
    """
    resultado = []

    for fila in filas:
        fila_nueva = dict(fila)
        fila_nueva["moneda"] = "colones"  # valor por defecto

        # Buscar el valor original de Saldo Actual para revisar el símbolo
        monto_original = None
        for clave, valor in fila.items():
            clave_lower = str(clave).lower()
            if "saldo" in clave_lower or "monto" in clave_lower or "cuota" in clave_lower:
                monto_original = valor
                break

        # Si no se encontró por nombre, buscar cualquier valor que tenga "$" o "₡"
        if monto_original is None:
            for clave, valor in fila.items():
                if isinstance(valor, str) and ("$" in valor or "₡" in valor):
                    monto_original = valor
                    break

        if isinstance(monto_original, str):
            if "$" in monto_original:
                fila_nueva["moneda"] = "dólares"
            else:
                fila_nueva["moneda"] = "colones"

        resultado.append(fila_nueva)

    return resultado
