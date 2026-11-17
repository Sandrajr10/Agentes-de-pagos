"""Servicios de lógica de negocio - Regla R2

R2: Asigna el banco de cada fila de sección a las filas de operación que le
siguen hasta que aparezca la siguiente sección de banco.
"""


def asignar_bancos(filas: list[dict]) -> list[dict]:
    """Asigna el banco de sección a cada fila de operación.

    Las filas de sección tienen el nombre del banco en la primera columna
    y el resto de columnas vacías. Las filas de operación tienen datos
    en la columna de N° Operación o en columnas de monto/fecha.

    Args:
        filas: Lista de diccionarios con las filas crudas del Excel.

    Returns:
        Lista de diccionarios con una clave adicional 'banco' en cada fila
        de operación. Las filas de sección se conservan con su nombre en
        'nombre_banco' y se marcan como es_seccion=True.
    """
    resultado = []
    banco_actual = None

    for fila in filas:
        # Detectar si es fila vacía completa
        if all(str(v).strip() == "" for v in fila.values()):
            continue

        primera_columna = list(fila.values())[0] if fila else ""
        otras_columnas = list(fila.values())[1:]

        # Es fila de sección si: primera columna tiene texto y el resto está vacía
        es_seccion = (
            str(primera_columna).strip() != ""
            and all(str(v).strip() == "" for v in otras_columnas)
        )

        if es_seccion:
            banco_actual = str(primera_columna).strip()
            resultado.append({
                **fila,
                "es_seccion": True,
                "nombre_banco": banco_actual,
                "banco": banco_actual,
            })
        else:
            # Es fila de operación
            resultado.append({
                **fila,
                "es_seccion": False,
                "banco": banco_actual,
            })

    return resultado
