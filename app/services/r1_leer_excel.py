"""Servicios de lógica de negocio - Regla R1

R1: La app lee el archivo de operaciones en la carpeta insumos.
"""

import os
import pandas as pd


def leer_excel_operaciones(ruta_archivo: str) -> list[dict]:
    """Lee el archivo Excel de operaciones y devuelve una lista de diccionarios
    con las filas crudas del archivo.

    Args:
        ruta_archivo: Ruta al archivo .xlsx o .xls

    Returns:
        Lista de diccionarios, uno por fila, con las columnas originales.
        Si el archivo no existe o no se puede leer, devuelve lista vacía.
    """
    if not os.path.exists(ruta_archivo):
        return []

    try:
        df = pd.read_excel(ruta_archivo, header=None)
        filas = []
        for _, row in df.iterrows():
            fila = {str(col): ("" if pd.isna(val) else val) for col, val in row.items()}
            filas.append(fila)
        return filas
    except Exception:
        return []
