"""Servicios de lógica de negocio - Regla R1

R1: La app lee el archivo de operaciones en la carpeta insumos.

Soporta los dos encabezados que se usan en los archivos del negocio:
- Lista de operaciones: Número Operación, Monto Original, Saldo Actual,
  Tasa Interés, Próximo Pago, Fecha Constitución, Fecha Definitivo.
- Lista por banco: Banco, Fecha de apertura, Fecha de pago, Cuota,
  Monto cancelar, Vencimiento, Tasa.
"""

import os
import unicodedata
import warnings

import pandas as pd

# Nombres de las columnas definidas en AGENTS.md, con sus sinónimos. Se buscan
# por texto del encabezado para no depender de la posición exacta.
COLUMNAS_DEFINIDAS = {
    "numero_operacion": ("numero operacion", "n operacion", "operacion"),
    "banco": ("banco",),
    "monto_original": ("monto original",),
    "saldo_actual": ("saldo actual", "cuota"),
    "proximo_pago": ("proximo pago", "fecha de pago", "proximo vencimiento"),
    "fecha_constitucion": ("constitucion", "fecha de apertura"),
    "fecha_definitivo": ("definitivo", "vencimiento"),
    "tasa_interes": ("tasa",),
}


def _normalizar(valor) -> str:
    """Convierte un valor a texto en minúsculas, sin acentos ni espacios extra."""
    texto = str(valor).strip().lower()
    texto = " ".join(texto.replace("\xa0", " ").split())
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def _detectar_columnas(fila: dict) -> dict | None:
    """Identifica las columnas del archivo a partir de una fila de encabezado.

    Devuelve un diccionario {nombre_definido: clave_de_columna} o None si la
    fila no es un encabezado válido (debe tener la fecha de pago y el monto).
    """
    columnas = {}
    for clave, valor in fila.items():
        texto = _normalizar(valor)
        if not texto:
            continue
        for nombre, patrones in COLUMNAS_DEFINIDAS.items():
            if nombre in columnas:
                continue
            if any(patron in texto for patron in patrones):
                columnas[nombre] = clave
                break

    if "proximo_pago" in columnas and "saldo_actual" in columnas:
        return columnas
    return None


def _es_fila_de_titulo(fila: dict) -> bool:
    """Indica si la fila solo tiene texto en la primera columna y el resto vacío."""
    valores = list(fila.values())
    if not valores:
        return False
    return str(valores[0]).strip() != "" and all(str(v).strip() == "" for v in valores[1:])


def _crudas(df) -> list[dict]:
    """Convierte la hoja de pandas en filas con claves numéricas."""
    return [
        {str(col): ("" if pd.isna(val) else val) for col, val in row.items()}
        for _, row in df.iterrows()
    ]


def _ultima_fecha(hoja, columnas: dict):
    """Devuelve la fecha de pago más reciente de la hoja (o None)."""
    clave = columnas["proximo_pago"]
    columna = int(clave) if str(clave).isdigit() else clave
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            serie = pd.to_datetime(hoja[columna], errors="coerce")
        fechas = serie.dropna()
        if fechas.empty:
            return None
        return fechas.max()
    except Exception:
        return None


def _leer_hoja(df, columnas: dict | None = None) -> list[dict]:
    """Convierte una hoja de pandas en filas con las columnas ya identificadas."""
    crudas = _crudas(df)

    indice_encabezado = None
    if columnas is None:
        for i, fila in enumerate(crudas):
            detectadas = _detectar_columnas(fila)
            if detectadas:
                indice_encabezado = i
                columnas = detectadas
                break
    else:
        for i, fila in enumerate(crudas):
            if _detectar_columnas(fila) == columnas:
                indice_encabezado = i
                break

    filas = []
    for i, fila in enumerate(crudas):
        if indice_encabezado is not None:
            # No procesar la fila de encabezado
            if i == indice_encabezado:
                continue
            # El texto que está justo encima del encabezado es un subtítulo,
            # no un nombre de banco.
            if i == indice_encabezado - 1 and _es_fila_de_titulo(fila):
                continue
            # Agregar los nombres de columna definidos
            if i > indice_encabezado:
                for nombre, clave in columnas.items():
                    fila[nombre] = fila.get(clave, "")

        filas.append(fila)

    return filas


def leer_excel_operaciones(ruta_archivo: str) -> list[dict]:
    """Lee el archivo Excel de operaciones y devuelve una lista de diccionarios
    con las filas crudas del archivo.

    Busca las hojas que tengan un encabezado conocido (fecha de pago y monto).
    Si hay varias, usa la que tenga la fecha de pago más reciente, para no
    procesar hojas viejas del mismo libro. Si ninguna tiene encabezado
    conocido, usa la primera hoja.

    Args:
        ruta_archivo: Ruta al archivo .xlsx o .xls

    Returns:
        Lista de diccionarios, uno por fila. Las filas de operación traen
        además las claves 'numero_operacion', 'banco', 'saldo_actual',
        'proximo_pago', etc. Si el archivo no existe o no se puede leer,
        devuelve lista vacía.
    """
    if not os.path.exists(ruta_archivo):
        return []

    try:
        with pd.ExcelFile(ruta_archivo) as xls:
            hojas = list(xls.sheet_names)

            candidatas = []
            for nombre_hoja in hojas:
                vista = pd.read_excel(xls, sheet_name=nombre_hoja, header=None, nrows=40)
                for _, row in vista.iterrows():
                    fila = {str(col): ("" if pd.isna(val) else val) for col, val in row.items()}
                    columnas = _detectar_columnas(fila)
                    if columnas:
                        candidatas.append((nombre_hoja, columnas))
                        break

            if not candidatas:
                return _leer_hoja(pd.read_excel(xls, sheet_name=hojas[0], header=None))

            elegida = None
            for nombre_hoja, columnas in candidatas:
                hoja = pd.read_excel(xls, sheet_name=nombre_hoja, header=None)
                ultima = _ultima_fecha(hoja, columnas)
                if elegida is None or (ultima is not None and (elegida["ultima"] is None or ultima > elegida["ultima"])):
                    elegida = {"hoja": hoja, "ultima": ultima}

        return _leer_hoja(elegida["hoja"])
    except Exception as e:
        print(f"[R1] No se pudo leer el Excel '{ruta_archivo}': {e}", flush=True)
        return []
