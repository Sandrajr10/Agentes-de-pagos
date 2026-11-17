"""Servicios de lógica de negocio - Regla R8

R8: Si `N° Operación` está vacío, la fila se omite.
"""


def omitir_sin_numero_operacion(filas: list[dict]) -> list[dict]:
    """Omite las filas que no tienen N° Operación.

    Args:
        filas: Lista de diccionarios con las filas de operación.

    Returns:
        Lista de diccionarios solo con filas que tienen N° Operación no vacío.
    """
    resultado = []

    for fila in filas:
        # Saltar filas de sección
        if fila.get("es_seccion"):
            resultado.append(fila)
            continue

        # Buscar el valor de N° Operación
        num_operacion = None
        for clave, valor in fila.items():
            clave_lower = str(clave).lower()
            if "operación" in clave_lower or "operacion" in clave_lower or "número" in clave_lower or "numero" in clave_lower:
                num_operacion = valor
                break

        # Si no se encontró por nombre de columna, usar la primera columna
        if num_operacion is None and len(fila) > 0:
            primera_clave = list(fila.keys())[0]
            num_operacion = fila[primera_clave]

        if num_operacion is None or str(num_operacion).strip() == "":
            # Omitir esta fila (no se agrega al resultado)
            continue

        resultado.append(fila)

    return resultado
