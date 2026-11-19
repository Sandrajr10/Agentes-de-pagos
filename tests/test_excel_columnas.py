"""Pruebas de regresión con un archivo Excel real generado en tiempo de prueba.

Cubren los errores que hacían que la app mostrara 0 operaciones:
- No se podía leer el .xlsx (faltaba openpyxl).
- Las columnas se adivinaban por valor: tomaba Monto Original en vez de
  Saldo Actual y Fecha Constitución en vez de Próximo Pago.
"""

import sys
import os
from datetime import date, timedelta

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


CABECERA = [
    "Número Operación",
    "Monto Original",
    "Saldo Actual",
    "Tasa Interés",
    "Próximo Pago",
    "Fecha Constitución",
    "Fecha Definitivo",
]


def _crear_excel(ruta, filas_operacion):
    """Crea un Excel con la misma estructura del archivo de insumos."""
    datos = [
        [None] * 7,
        ["Banco Costa Rica"] + [None] * 6,
        ["Consulta de mis Créditos"] + [None] * 6,  # subtítulo
        CABECERA,
    ]
    datos.extend(filas_operacion)
    datos.append(["SCOTIABANK"] + [None] * 6)
    datos.append([
        "430000048722",
        "$2,000,000.00",
        "$1,666,666.67",
        "0.055",
        "2023-05-25",
        "2023-04-25",
        "2027-09-25",
    ])
    pd.DataFrame(datos).to_excel(ruta, index=False, header=False)


def _fila(numero, proximo_pago, saldo="$750,000.00", monto_original="$1,500,000.00"):
    return [
        numero,
        monto_original,
        saldo,
        "2.050%M/V",
        proximo_pago,
        "2023-01-25",
        "2027-07-25",
    ]


def _procesar(ruta):
    filas = leer_excel_operaciones(ruta)
    filas = asignar_bancos(filas)
    filas = calcular_dias_para_vencer(filas)
    validas, errores = reportar_fechas_invalidas(filas)
    validas = omitir_sin_numero_operacion(validas)
    return filas, validas, errores


def test_lee_archivo_xlsx_y_asigna_banco(tmp_path):
    """R1/R2: el .xlsx se lee y las operaciones heredan el banco de la sección."""
    ruta = tmp_path / "operaciones.xlsx"
    _crear_excel(ruta, [_fila("OP-1", "2026-11-19")])

    filas, validas, _ = _procesar(str(ruta))

    assert len(filas) > 0
    por_numero = {f["0"]: f["banco"] for f in validas if not f.get("es_seccion")}
    assert por_numero["OP-1"] == "Banco Costa Rica"
    assert por_numero["430000048722"] == "SCOTIABANK"


def test_usa_proximo_pago_y_no_fecha_constitucion(tmp_path):
    """R3/R7: con Próximo Pago '--/--/----' la fila es error, aunque
    Fecha Constitución y Fecha Definitivo tengan fechas válidas."""
    ruta = tmp_path / "operaciones.xlsx"
    _crear_excel(ruta, [_fila("OP-MALA", "--/--/----")])

    _, validas, errores = _procesar(str(ruta))

    assert len(errores) == 1
    assert errores[0]["0"] == "OP-MALA"
    assert all(op["0"] != "OP-MALA" for op in validas)


def test_usa_saldo_actual_y_no_monto_original(tmp_path):
    """R5: el monto a pagar se toma de Saldo Actual."""
    ruta = tmp_path / "operaciones.xlsx"
    _crear_excel(ruta, [_fila("OP-1", "2026-11-19")])

    _, validas, _ = _procesar(str(ruta))
    operaciones = extraer_monto(validas)
    operacion = [op for op in operaciones if op["0"] == "OP-1"][0]

    assert operacion["monto"] == 750000.0


def test_detecta_moneda_por_simbolo_de_saldo_actual(tmp_path):
    """R6: '$' en Saldo Actual son dólares; sin símbolo son colones."""
    ruta = tmp_path / "operaciones.xlsx"
    _crear_excel(
        ruta,
        [
            _fila("OP-USD", "2026-11-19", saldo="$750,000.00"),
            _fila("OP-CRC", "2026-11-19", saldo="750000.00"),
        ],
    )

    _, validas, _ = _procesar(str(ruta))
    operaciones = detectar_moneda(validas)

    monedas = {op["0"]: op["moneda"] for op in operaciones}
    assert monedas["OP-USD"] == "dólares"
    assert monedas["OP-CRC"] == "colones"


def test_detecta_avisos_a_7_y_1_dia(tmp_path):
    """R4/R9: solo se avisa a 7 y a 1 día; vencidas y lejanas se ignoran."""
    ruta = tmp_path / "operaciones.xlsx"
    hoy = hoy_en_costa_rica()
    _crear_excel(
        ruta,
        [
            _fila("OP-7", hoy + timedelta(days=7)),
            _fila("OP-1", hoy + timedelta(days=1)),
            _fila("OP-0", hoy),
            _fila("OP-VENCIDA", hoy - timedelta(days=17)),
            _fila("OP-15", hoy + timedelta(days=15)),
        ],
    )

    _, validas, _ = _procesar(str(ruta))
    avisos = filtrar_operaciones_por_vencer(validas)

    numeros = {op["0"] for op in avisos}
    assert numeros == {"OP-7", "OP-1"}
    assert {"OP-0", "OP-VENCIDA", "OP-15"}.isdisjoint(numeros)
