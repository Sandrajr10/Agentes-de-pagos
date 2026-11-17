# PLAN.md

## 1. RESUMEN

Vamos a construir una app web en Python/Flask que lea un Excel de operaciones bancarias y avise por correo al jefe cuándo una operación vence en 7 días o en 1 día. Entra el archivo `Insumos\LISTA DE OPERACIONES2.xlsx` con columnas de banco (por sección), monto (Saldo Actual), fecha de vencimiento (Próximo Pago) y otros campos ignorados. El agente de IA interpreta la moneda y redacta el aviso. Sale una pantalla con tabla de operaciones por vencer, botón de envío de correo y mensajes de error si hay filas incompletas.

## 2. LO QUE ENCONTRÉ

**Carpeta `contexto/`:** contiene `Contexto_Mi_App.md` (extraído del Word). Es un prompt para agente IA con reglas de notificación (alerta crítica 24h, alerta semanal 7 días), formato de tabla con 6 columnas y restricciones de "cero suposiciones".

**Carpeta `insumos/`:** contiene `LISTA DE OPERACIONES2.xlsx`. Tiene 20 filas y 7 columnas: `N° Operación`, `Monto Original`, `Saldo Actual`, `Tasa Interés`, `Próximo Pago`, `Fecha Constitución`, `Fecha Definitivo`. El banco aparece en filas de sección (no por fila). Algunas filas tienen `Próximo Pago = "--/--/----"` y algunas tienen `N° Operación` vacío.

**¿Coincide con `AGENTS.md`?** Parcialmente:
- `AGENTS.md` usa `Saldo Actual` como monto y `Próximo Pago` como fecha de vencimiento: sí están en el Excel.
- `AGENTS.md` ignora `Monto Original`, `Tasa Interés`, `Fecha Constitución`, `Fecha Definitivo`: sí están en el Excel pero se ignoran.
- `AGENTS.md` contempla que el banco viene en filas de sección: coincide con el Excel.
- Falta confirmar: símbolo exacto para dólares (¿"$" o "USD"?), servidor SMTP y credenciales de correo, si la revisión se ejecuta una vez al día o cada cierto tiempo, y si se necesita un archivo de prueba específico con cifras de control exactas.

## 3. ENTREGAS POR SUBAGENTE

| N° | Responsable | Qué debe entregar | Archivos que crea o modifica | Qué recibe de la entrega anterior | Cómo se verifica en pantalla |
|----|-------------|-------------------|------------------------------|-----------------------------------|------------------------------|
| 1 | @backend | Estructura base Flask con `uv`: `app/__init__.py` con `create_app()`, `wsgi.py`, `iniciar_app.bat`, archivo `.env` vacío para la llave del agente | `app/__init__.py`, `wsgi.py`, `iniciar_app.bat`, `.env` | Ninguna (inicio del proyecto) | Ejecutar `iniciar_app.bat`, la app abre en `http://localhost:5000` y muestra la pantalla de inicio |
| 2 | @backend | R1: Función que lee el archivo Excel `Insumos\LISTA DE OPERACIONES2.xlsx` y devuelve las filas crudas | `app/services/` (nueva función con comentario R1) | Ninguna | Al subir el Excel en la pantalla de inicio, la app lee el archivo sin error |
| 3 | @backend | R2: Función que asigna el banco de cada fila de sección a las filas de operación que le siguen hasta la siguiente sección | `app/services/` (nueva función con comentario R2) | Filas crudas de la entrega R1 | En la tabla de resultados, cada operación muestra su banco asignado correctamente |
| 4 | @backend | R3: Función que calcula días entre fecha actual y `Próximo Pago` | `app/services/` (nueva función con comentario R3) | Filas con banco asignado (entrega R2) | La pantalla muestra los días restantes calculados para cada operación |
| 5 | @backend | R4 + R9: Función que marca solo operaciones con exactamente 7 días o exactamente 1 día para vencer; ignora vencidos y >7 días | `app/services/` (nueva función con comentario R4/R9) | Días calculados (entrega R3) | La tabla solo muestra operaciones que faltan 7 días o 1 día; las demás no aparecen |
| 6 | @backend | R5: Función que extrae el monto a pagar de `Saldo Actual` | `app/services/` (nueva función con comentario R5) | Filas filtradas (entrega R4/R9) | La tabla muestra el monto numérico correcto de Saldo Actual |
| 7 | @backend | R6: Función que detecta moneda por símbolo "$" en `Saldo Actual` (dólares) o sin símbolo (colones) | `app/services/` (nueva función con comentario R6) | Filas con monto (entrega R5) | La tabla muestra "dólares" o "colones" según el símbolo de la celda |
| 8 | @backend | R7: Función que reporta como error filas con `Próximo Pago = "--/--/----"` o vacío, y no las procesa | `app/services/` (nueva función con comentario R7) | Filas con moneda (entrega R6) | En pantalla aparece un mensaje de error indicando qué filas tienen fecha inválida |
| 9 | @backend | R8: Función que omite filas con `N° Operación` vacío | `app/services/` (nueva función con comentario R8) | Filas con fecha válida (entrega R7) | Las filas con N° Operación vacío no aparecen en la tabla ni generan error |
| 10 | @backend | R10: Configurar destinatario de correo `sandra.jimenez@montecillos.com` y endpoint de envío | `app/controllers/` (nueva ruta de envío), `app/services/` (función de envío) | Datos finales para aviso (entregas R5-R8) | Al hacer clic en "Enviar aviso", se muestra confirmación de envío a esa dirección |
| 11 | @backend | Integración del agente de IA: llama al agente pasando banco, Saldo Actual (con símbolo), fecha de vencimiento, días restantes; respeta contrato JSON; lee llave de `.env` | `app/services/` (nueva función de integración IA), `.env` (llave real) | Datos procesados (entregas R2-R8) | La pantalla muestra el mensaje redactado por el agente con moneda y monto correctos |
| 12 | @frontend | Pantalla de inicio: botón de carga para archivo Excel, pantalla vacía inicial | `app/templates/inicio.html`, `app/templates/base.html` (CSS embebido) | Ninguna | Al abrir la app se ve un botón "Cargar Excel" y un campo de selección de archivo |
| 13 | @frontend | Pantalla de resultados: tablero con contadores grandes (total operaciones, por vencer, errores) y tabla con filtro | `app/templates/resultados.html`, `app/static/` si es necesario | Datos procesados del backend (entregas R2-R11) | Al cargar el Excel se ve la tabla con banco, moneda, monto, días restantes y contadores arriba |
| 14 | @frontend | Detalle por registro: al hacer clic en una fila de la tabla se ve el detalle completo de esa operación | `app/templates/resultados.html` (modificación) | Tabla de resultados (entrega 13) | Al hacer clic en una fila se expande o abre una vista con todos los campos de esa operación |
| 15 | @frontend | Estilo de la app: CSS embebido en `base.html`, todo en español, pantallas sencillas y profesionales, sin librerías JS externas | `app/templates/base.html` | Plantillas anteriores | La app se ve coherente, en español, sin librerías JS externas cargadas |
| 16 | @tester | Pruebas en `tests/` con `pytest` contra las cifras de control y casos límite de `AGENTS.md`; archivo `VALIDACION.md` con esperado vs obtenido | `tests/test_*.py`, `VALIDACION.md`, `pytest.ini` o `conftest.py` | App completa (entregas 1-15) | Ejecutar `pytest` y ver cuántas pruebas pasan/failan; `VALIDACION.md` muestra tabla esperado vs obtenido |
| 17 | @revisor | Revisión de seguridad: llaves no en código, `.env` en `.gitignore`, datos sensibles no expuestos; revisión de que todo esté en `AGENTS.md` | Informe de hallazgos (archivo `.md` o texto) | Código completo (entregas 1-16) | El revisor entrega una lista de hallazgos con prioridad y corrección propuesta |

## 4. PUNTOS DE CONTROL

| Después de la entrega | Quién interviene | Qué debo ver en pantalla exactamente |
|----------------------|------------------|--------------------------------------|
| 1 | @tester | La app arranca en `http://localhost:5000` y muestra la pantalla de inicio con botón "Cargar Excel" |
| 12 | @tester | Al abrir la URL se ve el botón de carga y el input de archivo sin errores de plantilla |
| 13 | @tester | Al cargar un Excel de prueba, la tabla muestra solo operaciones con 7 días o 1 día de vencimiento; contadores grandes muestran totales correctos |
| 17 | @revisor | No hay llaves escritas en el código; `.env` está en `.gitignore`; no hay datos sensibles en logs |

## 5. RIESGOS

| Riesgo | Qué hará cada subagente si pasa |
|--------|--------------------------------|
| Datos incompletos (fila sin banco, sin fecha, sin monto) | @backend aplica R7/R8: reporta error o omite la fila. @frontend muestra el mensaje de error en pantalla. @tester valida que no se procese. |
| Archivo escaneado o sin texto legible | @backend reporta error de lectura en pantalla (no se puede extraer texto de imagen). @frontend muestra aviso de "archivo no legible". |
| Respuesta del agente de IA que no es JSON válido | @backend debe manejar la excepción y mostrar "no indicado" en los campos que falten, sin romper la app. @revisor verifica que no se inventen datos. |
| Límite de la llave gratis del agente de IA | @backend muestra mensaje en pantalla: "Llave del agente agotada o inválida". @revisor verifica que la llave solo esté en `.env`. |
| Columnas que no están en AGENTS.md | Cualquier subagente se detiene y pregunta al usuario antes de continuar. |
| Fechas con formato `--/--/----` | @backend aplica R7: reporta como error y no procesa esa fila. |

## 6. PREGUNTAS PARA MÍ

Respuestas confirmadas:

1. El símbolo para dólares es `"$"`.
2. **Pendiente:** servidor SMTP y credenciales para enviar los correos a `sandra.jimenez@montecillos.com`.
3. La revisión de vencimientos se ejecuta una vez al día, en la mañana.
4. Ya existe un archivo Excel de prueba con cifras de control exactas.
5. Sí, sin símbolo se trata como colones.

Cuando me dé las credenciales de SMTP (pregunta 2), puedo comenzar a repartir las entregas a los subagentes.
