"""Pruebas de las reglas de negocio del proyecto AvisoVencimientoBancario.

Estas pruebas validan los servicios R1-R9 usando datos de prueba sintéticos,
sin depender de archivos Excel reales.
"""

import sys
import os
from datetime import date, timedelta

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


# ---------------------------------------------------------------------------
# Datos de prueba sintéticos (fila por fila, como saldrían de R1)
# ---------------------------------------------------------------------------

FILAS_PRUEBA = [
    # Fila de sección Banco A
    {"0": "Banco A", "1": "", "2": "", "3": "", "4": "", "5": "", "6": "", "es_seccion": False, "banco": None},
    # Operación 1: vence en 7 días, dólares
    {"0": "OP-001", "1": "$1000", "2": "$500", "3": "5%", "4": None, "5": "", "6": "", "es_seccion": False, "banco": None},
    # Operación 2: vence en 1 día, colones
    {"0": "OP-002", "1": "₡100000", "2": "₡50000", "3": "6%", "4": None, "5": "", "6": "", "es_seccion": False, "banco": None},
    # Operación 3: ya venció
    {"0": "OP-003", "1": "$2000", "2": "$1000", "3": "7%", "4": None, "5": "", "6": "", "es_seccion": False, "banco": None},
    # Operación 4: vence en 15 días (ignorar)
    {"0": "OP-004", "1": "₡200000", "2": "₡100000", "3": "8%", "4": None, "5": "", "6": "", "es_seccion": False, "banco": None},
    # Operación 5: fecha inválida --/--/----
    {"0": "OP-005", "1": "$3000", "2": "$1500", "3": "9%", "4": "--/--/----", "5": "", "6": "", "es_seccion": False, "banco": None},
    # Operación 6: sin N° Operación (debe omitirse)
    {"0": "", "1": "$4000", "2": "$2000", "3": "10%", "4": None, "5": "", "6": "", "es_seccion": False, "banco": None},
]


def preparar_filas_con_fecha(fecha_str: str):
    """Copia las filas de prueba y les asigna la fecha de vencimiento dada."""
    filas = []
    for f in FILAS_PRUEBA:
        nueva = dict(f)
        nueva["4"] = fecha_str  # columna Próximo Pago
        filas.append(nueva)
    return filas


def test_r1_leer_excel_archivo_inexistente():
    """R1: Archivo inexistente debe devolver lista vacía."""
    resultado = leer_excel_operaciones("ruta_que_no_existe.xlsx")
    assert resultado == []


def test_r2_asignar_banco_a_operaciones():
    """R2: Las filas de operación deben heredar el banco de la sección."""
    filas = [
        {"0": "Banco X", "1": "", "2": "", "3": "", "4": "", "5": "", "6": ""},
        {"0": "OP-100", "1": "$100", "2": "$50", "3": "5%", "4": "2026-01-15", "5": "", "6": ""},
    ]
    resultado = asignar_bancos(filas)
    operacion = [f for f in resultado if not f.get("es_seccion")][0]
    assert operacion["banco"] == "Banco X"


def test_r3_calcular_dias_7_dias():
    """R3: Fecha en 7 días debe reportar 7 días restantes."""
    hoy = hoy_en_costa_rica()
    fecha_futura = hoy + timedelta(days=7)
    filas = [
        {"0": "OP-1", "1": "", "2": "", "3": "", "4": fecha_futura.strftime("%Y-%m-%d"), "5": "", "6": ""}
    ]
    resultado = calcular_dias_para_vencer(filas)
    assert resultado[0]["dias_para_vencer"] == 7


def test_r3_calcular_dias_1_dia():
    """R3: Fecha en 1 día debe reportar 1 día restante."""
    hoy = hoy_en_costa_rica()
    fecha_mañana = hoy + timedelta(days=1)
    filas = [
        {"0": "OP-1", "1": "", "2": "", "3": "", "4": fecha_mañana.strftime("%Y-%m-%d"), "5": "", "6": ""}
    ]
    resultado = calcular_dias_para_vencer(filas)
    assert resultado[0]["dias_para_vencer"] == 1


def test_r4_filtrar_solo_7_y_1_dia():
    """R4/R9: Solo operaciones con 7 o 1 día deben pasar el filtro."""
    hoy = date.today()
    filas = [
        {"0": "OP-1", "dias_para_vencer": 7, "es_seccion": False, "banco": "Banco A"},
        {"0": "OP-2", "dias_para_vencer": 1, "es_seccion": False, "banco": "Banco B"},
        {"0": "OP-3", "dias_para_vencer": 0, "es_seccion": False, "banco": "Banco C"},  # ya venció
        {"0": "OP-4", "dias_para_vencer": 15, "es_seccion": False, "banco": "Banco D"},  # >7 días
        {"0": "OP-5", "dias_para_vencer": None, "es_seccion": False, "banco": "Banco E"},  # fecha inválida
    ]
    resultado = filtrar_operaciones_por_vencer(filas)
    assert len(resultado) == 2
    assert all(op["dias_para_vencer"] in (7, 1) for op in resultado)


def test_r5_extraer_monto_con_simbolo_dolar():
    """R5: Monto con símbolo $ debe extraerse como número."""
    filas = [
        {"0": "OP-1", "1": "$1,500.00", "es_seccion": False, "banco": "Banco A"}
    ]
    resultado = extraer_monto(filas)
    assert resultado[0]["monto"] == 1500.0


def test_r5_extraer_monto_sin_simbolo():
    """R5: Monto sin símbolo también debe extraerse."""
    filas = [
        {"0": "OP-1", "1": "500000", "es_seccion": False, "banco": "Banco A"}
    ]
    resultado = extraer_monto(filas)
    assert resultado[0]["monto"] == 500000.0


def test_r6_detectar_moneda_dolares():
    """R6: Símbolo $ indica dólares."""
    filas = [
        {"0": "OP-1", "1": "$500", "es_seccion": False, "banco": "Banco A"}
    ]
    resultado = detectar_moneda(filas)
    assert resultado[0]["moneda"] == "dólares"


def test_r6_detectar_moneda_colones():
    """R6: Sin símbolo $ indica colones."""
    filas = [
        {"0": "OP-1", "1": "500000", "es_seccion": False, "banco": "Banco A"}
    ]
    resultado = detectar_moneda(filas)
    assert resultado[0]["moneda"] == "colones"


def test_r7_reportar_fecha_invalida():
    """R7: Fecha --/--/---- debe ir a filas_con_error."""
    filas = [
        {"0": "OP-1", "4": "--/--/----", "es_seccion": False, "banco": "Banco A",
         "dias_para_vencer": None, "fecha_vencimiento": None}
    ]
    validas, errores = reportar_fechas_invalidas(filas)
    assert len(validas) == 0
    assert len(errores) == 1
    assert "motivo_error" in errores[0]


def test_r8_omitir_sin_numero_operacion():
    """R8: Filas con N° Operación vacío deben omitirse."""
    filas = [
        {"0": "", "1": "$500", "es_seccion": False, "banco": "Banco A"},
        {"0": "OP-001", "1": "$500", "es_seccion": False, "banco": "Banco A"},
    ]
    resultado = omitir_sin_numero_operacion(filas)
    assert len(resultado) == 1
    assert resultado[0]["0"] == "OP-001"
