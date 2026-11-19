"""Servicios de lógica de negocio - Regla R5

R5: Extrae el monto a pagar de la columna `Saldo Actual`.
"""

import re


def _limpiar_numero(texto: str) -> str:
    """Convierte un monto con formato costarricense a un número simple.

    Los archivos usan punto como separador de miles y también como decimal
    ("$8.635.70" son 8 635,70), espacios o comas como separador de miles, y a
    veces símbolos de moneda.
    """
    texto = texto.replace("\xa0", " ").replace("\u202f", " ")
    texto = re.sub(r"[^0-9.,]", "", texto)
    if "," in texto:
        texto = texto.replace(",", "")

    partes = texto.split(".")
    if len(partes) == 1:
        return texto

    ultima = partes[-1]
    resto = "".join(partes[:-1])
    # "1.234.567" son un millón doscientos..., no 1.234567
    if len(ultima) == 3 and len(partes) > 2:
        return resto + ultima
    return resto + "." + ultima


def _es_valor_monetario(valor) -> bool:
    """Determina si un valor parece un monto monetario."""
    if isinstance(valor, (int, float)):
        return True
    if isinstance(valor, str):
        limpio = _limpiar_numero(valor)
        if limpio in ("", "."):
            return False
        try:
            float(limpio)
            return True
        except ValueError:
            return False
    return False


def _extraer_numero_monto(valor) -> float | None:
    """Extrae el número flotante de un valor monetario."""
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        limpio = _limpiar_numero(valor)
        if limpio in ("", "."):
            return None
        try:
            return float(limpio)
        except ValueError:
            return None
    return None


def _buscar_valor_monto(fila: dict):
    """Busca el valor de monto en la fila.

    Si la fila trae la columna 'saldo_actual' identificada desde el encabezado
    del Excel, se usa esa columna (R5). Si no, busca por nombre de columna y,
    como último recurso, por el primer valor monetario.
    """
    if "saldo_actual" in fila:
        return fila.get("saldo_actual")

    # Primero por nombre de columna
    for clave, valor in fila.items():
        clave_lower = str(clave).lower()
        if any(palabra in clave_lower for palabra in ["saldo", "monto", "cuota"]):
            if _es_valor_monetario(valor):
                return valor

    # Fallback: buscar por valor monetario en columnas que no sean N° Operación
    # ni texto obvio de banco
    for clave, valor in fila.items():
        clave_str = str(clave)
        # Saltar la primera columna (generalmente N° Operación o nombre de banco)
        if clave_str == "0":
            continue
        if _es_valor_monetario(valor):
            return valor

    return None


def extraer_monto(filas: list[dict]) -> list[dict]:
    """Extrae el monto numérico de Saldo Actual de cada operación.

    El valor en el Excel puede venir con símbolo de moneda ($ o ₡),
    comas como separador de miles y punto decimal. Esta función limpia
    esos caracteres y devuelve un número float.

    Args:
        filas: Lista de diccionarios con las filas de operación.

    Returns:
        Lista de diccionarios con clave adicional 'monto' (float o None).
    """
    resultado = []

    for fila in filas:
        fila_nueva = dict(fila)
        fila_nueva["monto"] = None

        monto_valor = _buscar_valor_monto(fila)

        if monto_valor is None:
            resultado.append(fila_nueva)
            continue

        monto_numerico = _extraer_numero_monto(monto_valor)
        fila_nueva["monto"] = monto_numerico

        resultado.append(fila_nueva)

    return resultado
