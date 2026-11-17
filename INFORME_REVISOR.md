# Informe de Revisión - AvisoVencimientoBancario

Fecha de revisión: al completar las entregas 1-16.
Revisor: subagente @revisor (sin modificar nada).

## Resumen

Se revisó el código y las plantillas del proyecto en busca de:
- Reglas mal aplicadas respecto a AGENTS.md
- Datos sensibles expuestos
- Llaves o claves escritas en el código
- Archivos que no deberían subirse a GitHub
- Cualquier cosa que no esté definida en AGENTS.md

## Hallazgos

| Prioridad | Archivo y línea | Descripción | Corrección propuesta |
|-----------|-----------------|-------------|----------------------|
| Alta | `.env` (no tiene .gitignore) | El archivo `.env` contiene la llave del agente de IA y no está excluido del control de versiones. Si se sube a GitHub, se expone la llave. | Crear archivo `.gitignore` que incluya `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `flask.log`. |
| Media | `app/__init__.py` línea 15 | `SECRET_KEY` tiene un valor por defecto "dev-secret-key" si no está en .env. En producción debería obligarse a definirlo en .env. | Validar que `SECRET_KEY` exista en .env y lanzar error si falta, en lugar de usar valor por defecto. |
| Media | `app/controllers/__init__.py` | El envío de correo (ruta `/enviar-aviso`) prepara el mensaje pero no envía realmente porque faltan las credenciales SMTP. El usuario debe confirmarlas. | Documentar en README que se necesitan credenciales SMTP para activar el envío real de correo. |
| Baja | `app/services/r11_agente_ia.py` | La integración con el agente de IA usa lógica local como fallback. Cuando se tenga la API key real, se debe reemplazar por la llamada externa. | Agregar comentario claro marcando dónde se debe integrar la llamada a la API externa del agente. |
| Baja | `app/services/r10_envio_correo.py` | La función `obtener_configuracion_correo()` lee variables de entorno SMTP que aún no están definidas en .env. | Agregar ejemplo de variables SMTP en un archivo `.env.example` (sin valores reales). |
| Baja | `pyproject.toml` | Campo `tool.uv.dev-dependencies` está deprecado según la advertencia de uv. | Migrar a `[dependency-groups.dev]` en una versión futura de uv. |

## Reglas de negocio (R1-R10)

Se verificó que todas las reglas de AGENTS.md están implementadas:

- ✅ R1: Lectura del Excel (`r1_leer_excel.py`)
- ✅ R2: Asignación de banco de sección (`r2_asignar_banco.py`)
- ✅ R3: Cálculo de días para vencer (`r3_calcular_dias.py`)
- ✅ R4: Filtrar solo 7 días y 1 día (`r4_filtrar_vencimientos.py`)
- ✅ R5: Extraer monto de Saldo Actual (`r5_extraer_monto.py`)
- ✅ R6: Detectar moneda por símbolo "$" (`r6_detectar_moneda.py`)
- ✅ R7: Reportar fechas inválidas (`r7_reportar_fechas_invalidas.py`)
- ✅ R8: Omitir filas sin N° Operación (`r8_omitir_sin_numero.py`)
- ✅ R9: Ignorar vencidos y >7 días (implícito en R4)
- ✅ R10: Destinatario sandra.jimenez@montecillos.com (`r10_envio_correo.py`)

## Contrato JSON del agente de IA

Se verificó que `r11_agente_ia.py` respeta el contrato definido en AGENTS.md:
- ✅ `banco`: texto
- ✅ `moneda`: texto ("dólares", "colones", "no indicado")
- ✅ `monto`: número o "no indicado"
- ✅ `mensaje`: texto
- ✅ `dias_para_vencer`: número o "no indicado"
- ✅ `tipo_alerta`: texto ("semana", "dia")

## Datos sensibles

- ✅ No hay números de cuenta, cédulas ni claves escritas en el código fuente.
- ✅ La llave del agente de IA se lee desde `.env` mediante `os.environ.get`.
- ✅ Las carpetas `insumos/` y `contexto/` no fueron modificadas.

## Archivos que no deberían subirse a GitHub

- ⚠️ `.env` - contiene configuración sensible (falta .gitignore)
- ⚠️ `.venv/` - entorno virtual de Python
- ⚠️ `__pycache__/` - caché de Python
- ⚠️ `flask.log` - log de la aplicación
- ⚠️ `*.pyc` - bytecode compilado

## Conclusión

El proyecto cumple con las reglas de AGENTS.md. El único hallazgo de prioridad Alta es la falta de `.gitignore` para proteger `.env`. Se recomienda crear ese archivo antes de subir el repositorio a GitHub.
