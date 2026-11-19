from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import os
import tempfile
import uuid
from functools import wraps

from app.services.r1_leer_excel import leer_excel_operaciones
from app.services.r2_asignar_banco import asignar_bancos
from app.services.r3_calcular_dias import calcular_dias_para_vencer
from app.services.r4_filtrar_vencimientos import filtrar_operaciones_por_vencer
from app.services.r5_extraer_monto import extraer_monto
from app.services.r6_detectar_moneda import detectar_moneda
from app.services.r7_reportar_fechas_invalidas import reportar_fechas_invalidas
from app.services.r8_omitir_sin_numero import omitir_sin_numero_operacion
from app.services.r10_envio_correo import (
    DESTINATARIO_JEFE,
    correo_configurado,
    describir_error,
    enviar_aviso_operacion,
    registrar_envio,
)
from app.services.r11_agente_ia import agente_ia_interpretar

main_bp = Blueprint("main", __name__)


def _credencial_configurada(nombre):
    """Lee una credencial de las variables de entorno y descarta espacios o
    comillas que se agreguen por error al configurarla en el servidor."""
    valor = os.environ.get(nombre, "").strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        valor = valor[1:-1].strip()
    return valor


def _contar_operaciones(filas):
    """Cuenta las filas que son operaciones (tienen N° Operación)."""
    total = 0
    for fila in filas:
        if fila.get("es_seccion"):
            continue
        numero = fila.get("numero_operacion", fila.get("0", ""))
        if str(numero).strip() != "":
            total += 1
    return total


def requiere_login(f):
    """Decorator que exige que el usuario haya iniciado sesión."""
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get("usuario_autenticado"):
            flash("Debe iniciar sesión para acceder.", "error")
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)
    return decorada


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    """Pantalla de login. Lee credenciales de variables de entorno."""
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "").strip()

        usuario_valido = _credencial_configurada("APP_USUARIO")
        clave_valida = _credencial_configurada("APP_CLAVE")

        if not usuario_valido or not clave_valida:
            print(
                "[login] Falta configurar APP_USUARIO y/o APP_CLAVE en las "
                "variables de entorno del servidor.",
                flush=True,
            )
            flash(
                "El servidor no tiene configuradas las variables APP_USUARIO y "
                "APP_CLAVE. Revisa el panel de Render.",
                "error",
            )
            return render_template("login.html")

        if usuario == usuario_valido and clave == clave_valida:
            session["usuario_autenticado"] = True
            flash("Inicio de sesión exitoso.", "exito")
            return redirect(url_for("main.inicio"))
        else:
            flash("Usuario o contraseña incorrectos.", "error")

    return render_template("login.html")


@main_bp.route("/salir")
def salir():
    """Cierra la sesión del usuario."""
    session.pop("usuario_autenticado", None)
    flash("Sesión cerrada.", "exito")
    return redirect(url_for("main.login"))


@main_bp.route("/")
@requiere_login
def inicio():
    """Pantalla principal con botón para cargar el archivo Excel."""
    return render_template("inicio.html")


@main_bp.route("/cargar", methods=["POST"])
@requiere_login
def cargar():
    """Recibe el archivo Excel subido, lo procesa con todas las reglas de negocio
    y guarda los resultados en la sesión para mostrarlos en la pantalla de resultados."""
    if "archivo" not in request.files:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("main.inicio"))

    archivo = request.files["archivo"]
    if archivo.filename == "":
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("main.inicio"))

    if not archivo.filename.endswith((".xlsx", ".xls")):
        flash("El archivo debe ser un Excel (.xlsx o .xls).", "error")
        return redirect(url_for("main.inicio"))

    # Guardar archivo temporalmente
    tmp_dir = tempfile.gettempdir()
    nombre_tmp = f"{uuid.uuid4().hex}_{archivo.filename}"
    ruta_tmp = os.path.join(tmp_dir, nombre_tmp)
    archivo.save(ruta_tmp)

    try:
        # R1: Leer Excel
        filas = leer_excel_operaciones(ruta_tmp)

        if not filas:
            flash(
                "No se pudo leer el archivo o no contiene operaciones. "
                "Verifique que sea un Excel válido.",
                "error",
            )
            return redirect(url_for("main.inicio"))

        # R2: Asignar bancos de sección
        filas = asignar_bancos(filas)

        # R3: Calcular días para vencer
        filas = calcular_dias_para_vencer(filas)

        # R7: Separar filas con fechas inválidas
        filas_validas, filas_error = reportar_fechas_invalidas(filas)

        # R8: Omitir filas sin N° Operación
        filas_validas = omitir_sin_numero_operacion(filas_validas)

        # R4/R9: Filtrar solo operaciones a 7 días o 1 día
        operaciones_para_aviso = filtrar_operaciones_por_vencer(filas_validas)

        # R5: Extraer monto
        operaciones_para_aviso = extraer_monto(operaciones_para_aviso)

        # R6: Detectar moneda
        operaciones_para_aviso = detectar_moneda(operaciones_para_aviso)

        # R11: Agente de IA - interpretar y redactar mensajes
        operaciones_finales = []
        for op in operaciones_para_aviso:
            contrato = agente_ia_interpretar(op)
            fecha = op.get("fecha_vencimiento")
            if hasattr(fecha, "strftime"):
                fecha = fecha.strftime("%d/%m/%Y")
            operaciones_finales.append({
                "banco": contrato["banco"],
                "moneda": contrato["moneda"],
                "monto": contrato["monto"],
                "dias_para_vencer": contrato["dias_para_vencer"],
                "tipo_alerta": contrato["tipo_alerta"],
                "fecha_vencimiento": fecha if fecha else "no indicado",
                "mensaje_ia": contrato["mensaje"],
            })

        # Contadores
        total_cargadas = _contar_operaciones(filas)
        contador_semana = sum(1 for op in operaciones_finales if op["tipo_alerta"] == "semana")
        contador_dia = sum(1 for op in operaciones_finales if op["tipo_alerta"] == "dia")
        contador_errores = len(filas_error)

        # Guardar en sesión
        session["operaciones"] = operaciones_finales
        session["total_operaciones"] = total_cargadas
        session["contador_semana"] = contador_semana
        session["contador_dia"] = contador_dia
        session["contador_errores"] = contador_errores
        session["errores"] = [
            f"Fila {i+1}: {e.get('motivo_error', 'Fecha inválida')}"
            for i, e in enumerate(filas_error)
        ]

        flash(f"Archivo procesado. Se detectaron {len(operaciones_finales)} operación(es) por vencer.", "exito")

    except Exception as e:
        flash(f"Error al procesar el archivo: {str(e)}", "error")
    finally:
        # Limpiar archivo temporal (si el sistema lo permite)
        try:
            if os.path.exists(ruta_tmp):
                os.remove(ruta_tmp)
        except OSError:
            pass

    return redirect(url_for("main.resultados"))


@main_bp.route("/resultados")
@requiere_login
def resultados():
    """Pantalla de resultados con tabla de operaciones por vencer."""
    operaciones = session.get("operaciones", [])
    total = session.get("total_operaciones", 0)
    contador_semana = session.get("contador_semana", 0)
    contador_dia = session.get("contador_dia", 0)
    contador_errores = session.get("contador_errores", 0)
    errores = session.get("errores", [])

    return render_template(
        "resultados.html",
        operaciones=operaciones,
        total_operaciones=total,
        contador_semana=contador_semana,
        contador_dia=contador_dia,
        contador_errores=contador_errores,
        errores=errores,
    )


@main_bp.route("/enviar-aviso", methods=["POST"])
@requiere_login
def enviar_aviso():
    """Envía un correo por cada operación por vencer al jefe."""
    operaciones = session.get("operaciones", [])
    if not operaciones:
        flash("No hay operaciones para enviar.", "error")
        return redirect(url_for("main.resultados"))

    if not correo_configurado():
        flash(
            "El correo no está configurado. Defina SMTP_SERVIDOR, SMTP_USUARIO y "
            "SMTP_CONTRASENA en las variables de entorno del servidor.",
            "error",
        )
        return redirect(url_for("main.resultados"))

    enviados = 0
    fallidos = 0
    primer_error = None
    for operacion in operaciones:
        try:
            enviar_aviso_operacion(operacion)
            registrar_envio(
                DESTINATARIO_JEFE,
                operacion.get("banco", ""),
                operacion.get("tipo_alerta", ""),
                True,
            )
            enviados += 1
        except Exception as e:
            if primer_error is None:
                primer_error = describir_error(e)
            registrar_envio(
                DESTINATARIO_JEFE,
                operacion.get("banco", ""),
                operacion.get("tipo_alerta", ""),
                False,
                str(e),
            )
            fallidos += 1

    if fallidos == 0:
        flash(f"Se enviaron {enviados} aviso(s) a {DESTINATARIO_JEFE}.", "exito")
    else:
        detalle = f" Detalle: {primer_error}" if primer_error else ""
        flash(
            f"Se enviaron {enviados} aviso(s) y {fallidos} fallaron. "
            f"Revise el registro de envíos.{detalle}",
            "error",
        )

    return redirect(url_for("main.resultados"))
