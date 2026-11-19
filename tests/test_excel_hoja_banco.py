"""Pruebas del formato "hoja por banco" (Banco, Fecha de pago, Cuota).

Es el formato que usa la hoja con las operaciones vigentes del libro, distinto
al de la lista con filas de sección.
"""

import sys
import os
from datetime import timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.r1_leer_excel import leer_excel_operaciones
from app.services.r2_asignar_banco import asignar_bancos
from app.services.r3_calcular_dias import calcular_dias_para_vencer
from app.services.r4_filtrar_vencimientos import filtrar_operaciones_por_vencer
from app.services.r5_extraer_monto import extraer_monto
from app.services.r6_detectar_moneda import detectar_moneda
from app.services.r7_reportar_fechas_invalidas import reportar_fechas_invalidas
from app.services.r8_omitir_sin_numero import omitir_sin_numero_operacion
from app.services.tiempo import hoy_en_costa_rica

CABECERA_HOJA_BANCO = [
    "Banco",
    "Fecha de apertura",
    "Fecha de pago",
    "Cuota",
    "Monto cancelar",
    "Vencimiento",
    "Tasa",
]


def _fila_banco(banco, fecha_pago, cuota):
    return [banco, "2026-01-05", fecha_pago, cuota, None, "2030-01-05", 0.05]


def _crear_libro(ruta, filas):
    hoy = hoy_en_costa_rica()

    hoja_vieja = [
        [None] * 7,
        ["Banco Costa Rica"] + [None] * 6,
        ["Número Operación", "Monto Original", "Saldo Actual", "Tasa Interés",
         "Próximo Pago", "Fecha Constitución", "Fecha Definitivo"],
        ["01-594-01-02-5994087", "₡6,050,000,000.00", "₡1,601,403,812.52",
         "10.270%M/V", "2023-05-29", "2019-08-28", "2031-08-29"],
    ]

    hoja_nueva = [
        [None] * 7,
        ["Lista de Operaciones Octubre 2026"] + [None] * 6,
        CABECERA_HOJA_BANCO,
    ]
    hoja_nueva.extend(filas)
    hoja_nueva.append(_fila_banco("BCR 9999999", hoy + timedelta(days=1), "₡1.000.000,00"))

    with pd.ExcelWriter(ruta, engine="openpyxl") as libro:
        pd.DataFrame(hoja_vieja).to_excel(libro, sheet_name="Operaciones", index=False, header=False)
        pd.DataFrame(hoja_nueva).to_excel(libro, sheet_name="Hoja1", index=False, header=False)


def _procesar(ruta):
    filas = leer_excel_operaciones(ruta)
    filas = asignar_bancos(filas)
    filas = calcular_dias_para_vencer(filas)
    validas, errores = reportar_fechas_invalidas(filas)
    validas = omitir_sin_numero_operacion(validas)
    return filas, validas, errores


def test_usa_la_hoja_con_las_fechas_mas_recientes(tmp_path):
    """R1: si hay varias hojas con encabezado, se usa la de fechas vigentes."""
    hoy = hoy_en_costa_rica()
    ruta = tmp_path / "libro.xlsx"
    _crear_libro(ruta, [
        _fila_banco("Davi leasing 4796", hoy + timedelta(days=1), "$8.635.70"),
    ])

    _, validas, _ = _procesar(str(ruta))
    bancos = {f.get("0") for f in validas}

    assert "Davi leasing 4796" in bancos
    assert "01-594-01-02-5994087" not in bancos


def test_banco_viene_en_la_fila(tmp_path):
    """R2: en este formato cada fila trae su propio banco."""
    hoy = hoy_en_costa_rica()
    ruta = tmp_path / "libro.xlsx"
    _crear_libro(ruta, [
        _fila_banco("BCR 6164611", hoy + timedelta(days=5), "39190707.8"),
    ])

    _, validas, _ = _procesar(str(ruta))
    bancos = {f["0"]: f["banco"] for f in validas}

    assert bancos["BCR 6164611"] == "BCR 6164611"


def test_montos_con_punto_de_miles(tmp_path):
    """R5: '$8.635.70' son 8 635,70 y ' 4 812 500.00 ' son 4 812 500,00."""
    hoy = hoy_en_costa_rica()
    ruta = tmp_path / "libro.xlsx"
    _crear_libro(ruta, [
        _fila_banco("Davi 4796", hoy + timedelta(days=2), "$8.635.70"),
        _fila_banco("Davibank 54682", hoy + timedelta(days=2), "\xa0\xa0  4 812 500.00 "),
        _fila_banco("BAC 95654", hoy + timedelta(days=2), "101.483.783.00"),
    ])

    _, validas, _ = _procesar(str(ruta))
    montos = {f["0"]: f["monto"] for f in extraer_monto(validas)}

    assert montos["Davi 4796"] == 8635.70
    assert montos["Davibank 54682"] == 4812500.00
    assert montos["BAC 95654"] == 101483783.00


def test_moneda_en_formato_hoja_banco(tmp_path):
    """R6: '$' son dólares; montos sin símbolo son colones."""
    hoy = hoy_en_costa_rica()
    ruta = tmp_path / "libro.xlsx"
    _crear_libro(ruta, [
        _fila_banco("Davi 4796", hoy + timedelta(days=2), "$8.635.70"),
        _fila_banco("BCR 6181708", hoy + timedelta(days=2), "68166666.66"),
    ])

    _, validas, _ = _procesar(str(ruta))
    monedas = {f["0"]: f["moneda"] for f in detectar_moneda(validas)}

    assert monedas["Davi 4796"] == "dólares"
    assert monedas["BCR 6181708"] == "colones"


def test_avisos_7_y_1_dia_en_formato_hoja_banco(tmp_path):
    """R4/R9: se avisa solo a 7 y a 1 día."""
    hoy = hoy_en_costa_rica()
    ruta = tmp_path / "libro.xlsx"
    _crear_libro(ruta, [
        _fila_banco("OP-MANANA", hoy + timedelta(days=1), "$108.410.93"),
        _fila_banco("OP-SEMANA", hoy + timedelta(days=7), "86086018.53"),
        _fila_banco("OP-VENCIDA", hoy - timedelta(days=15), "$6.836.68"),
        _fila_banco("OP-LEJOS", hoy + timedelta(days=20), "$1.414.17"),
    ])

    _, validas, _ = _procesar(str(ruta))
    avisos = filtrar_operaciones_por_vencer(validas)
    numeros = {op["0"] for op in avisos}

    assert {"OP-MANANA", "OP-SEMANA"}.issubset(numeros)
    assert {"OP-VENCIDA", "OP-LEJOS"}.isdisjoint(numeros)
