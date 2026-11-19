"""Servicios de lógica de negocio - Regla R3

R3: Calcula los días entre la fecha actual y la columna `Próximo Pago`.
"""

from datetime import datetime, date


def _es_fecha_valida(valor) -> bool:
    """Determina si un valor es una fecha parseable y no un texto como 'OP-001'."""
    if isinstance(valor, (datetime, date)):
        return True
    if isinstance(valor, str):
        s = valor.strip()
        if s == "" or s == "--/--/----":
            return False
        # Evitar valores que claramente no son fechas (códigos de operación)
        if "-" in s and not any(c.isdigit() for c in s.split("-")[0]):
            return False
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                datetime.strptime(s, fmt)
                return True
            except ValueError:
                continue
    return False


def _parsear_fecha(valor):
    """Intenta parsear un valor como fecha. Retorna un objeto date o None."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        s = valor.strip()
        if s == "" or s == "--/--/----":
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
    return None


def _buscar_valor_fecha(fila: dict):
    """Busca el valor de fecha en la fila.

    Si la fila trae la columna 'proximo_pago' identificada desde el encabezado
    del Excel, se usa esa columna y ninguna otra. Si no, busca por nombre de
    columna y, como último recurso, por valor que sea una fecha válida.
    """
    if "proximo_pago" in fila:
        return fila.get("proximo_pago")

    # Primero por nombre de columna
    for clave, valor in fila.items():
        clave_lower = str(clave).lower()
        if any(palabra in clave_lower for palabra in ["pago", "vencimiento", "fecha", "proximo"]):
            if _es_fecha_valida(valor):
                return valor

    # Fallback: buscar por valor que sea fecha válida
    for clave, valor in fila.items():
        if _es_fecha_valida(valor):
            return valor

    return None


def calcular_dias_para_vencer(filas: list[dict]) -> list[dict]:
    """Calcula los días restantes hasta el vencimiento de cada operación.

    Busca la columna de fecha de vencimiento (Próximo Pago) en cada fila.
    Si la fecha es inválida (--/--/----, vacía, o no parseable), asigna
    dias_para_vencer = None y se marcará como error en R7.

    Args:
        filas: Lista de diccionarios con las filas (con banco asignado).

    Returns:
        Lista de diccionarios con clave adicional 'dias_para_vencer'
        (entero o None) y 'fecha_vencimiento' (fecha parseada o None).
    """
    resultado = []

    for fila in filas:
        fila_nueva = dict(fila)
        fila_nueva["dias_para_vencer"] = None
        fila_nueva["fecha_vencimiento"] = None

        fecha_valor = _buscar_valor_fecha(fila)

        if fecha_valor is None:
            resultado.append(fila_nueva)
            continue

        fecha_parsed = _parsear_fecha(fecha_valor)

        if fecha_parsed is None:
            resultado.append(fila_nueva)
            continue

        fila_nueva["fecha_vencimiento"] = fecha_parsed
        hoy = date.today()
        dias = (fecha_parsed - hoy).days
        fila_nueva["dias_para_vencer"] = dias

        resultado.append(fila_nueva)

    return resultado
