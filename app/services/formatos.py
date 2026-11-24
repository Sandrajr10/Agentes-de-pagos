"""Formato de números para la pantalla y los correos."""


def formato_monto(monto, moneda=None) -> str:
    """Devuelve el monto con separador de miles y el símbolo de la moneda.

    Ejemplos: 108410.93 con "dólares" -> "$108,410.93";
              68166666.66 con "colones" -> "₡68,166,666.66".
    """
    if not isinstance(monto, (int, float)):
        return "no indicado"

    simbolo = ""
    if moneda == "dólares":
        simbolo = "$"
    elif moneda == "colones":
        simbolo = "₡"

    return f"{simbolo}{monto:,.2f}"
