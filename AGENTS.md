# AGENTS.md

## Qué es esta app

Aplicación web que avisa por correo electrónico al jefe cuándo una operación bancaria está por vencer, con 7 días de anticipación y con 1 día de anticipación. En cada aviso indica el banco, la moneda y el monto a pagar. La app lee un archivo Excel de operaciones, detecta vencimientos próximos y envía notificaciones para que el jefe no se olvide de las fechas de pago.

## Datos de entrada

| Archivo | Formato | Columnas / Campos |
|---|---|---|
| `Insumos\LISTA DE OPERACIONES2.xlsx` | Excel (.xlsx) | N° Operación, Monto Original, Saldo Actual, Tasa Interés, Próximo Pago, Fecha Constitución, Fecha Definitivo |

**Notas sobre el archivo de insumos:**
- El banco no es una columna por fila; aparece en filas de sección (ej. "Banco Costa Rica", "SCOTIABANK", "BAC SAN JOSE") y debe asignarse a cada fila de operación que le sigue hasta que aparezca el siguiente banco.
- El monto de pago es la columna **Saldo Actual**.
- La fecha de vencimiento es la columna **Próximo Pago**.
- La moneda se detecta por el símbolo en la columna de monto (Saldo Actual): "$" indica dólares, "₡" (sin símbolo de dólar) indica colones.
- Algunas filas tienen `Próximo Pago` como `--/--/----` (fecha inválida).
- Algunas filas tienen `N° Operación` vacío.
- Columnas `Monto Original`, `Tasa Interés`, `Fecha Constitución` y `Fecha Definitivo` están presentes pero se ignoran para este proceso.

## Reglas de negocio (código, sin IA)

R1. La app lee el archivo `Insumos\LISTA DE OPERACIONES2.xlsx`.
R2. Asigna el banco de cada fila de sección a las filas de operación que le siguen hasta la siguiente sección de banco.
R3. Calcula los días entre la fecha actual y la columna `Próximo Pago`.
R4. Marca para aviso solo las operaciones que faltan exactamente 7 días o exactamente 1 día para vencer.
R5. Extrae el monto a pagar de la columna `Saldo Actual`.
R6. Detecta la moneda por el símbolo de `Saldo Actual`: símbolo "$" indica dólares; sin símbolo "$" indica colones.
R7. Si `Próximo Pago` es `--/--/----` o está vacío, la fila se reporta como error y no se procesa.
R8. Si `N° Operación` está vacío, la fila se omite.
R9. No se envían avisos para operaciones que ya vencieron o que vencen en más de 7 días.
R10. El destinatario de los avisos es sandra.jimenez@montecillos.com.

## Lo que hace el agente de IA (contrato JSON)

**Rol:** Interpretar la moneda de cada operación y redactar el mensaje del aviso.

**Qué recibe:** banco, valor de Saldo Actual (con su símbolo), fecha de vencimiento, días restantes.

**Contrato JSON (salida del agente):**

| Llave | Tipo | Qué significa |
|---|---|---|
| banco | texto | Nombre del banco de la operación |
| moneda | texto | "dólares" si hay símbolo "$", "colones" si no hay símbolo "$", "no indicado" si no se puede determinar |
| monto | número | Valor numérico de Saldo Actual a pagar |
| mensaje | texto | Redacción del aviso para el jefe |
| dias_para_vencer | número | 7 o 1 |
| tipo_alerta | texto | "semana" o "dia" |

**Regla del agente:** nunca inventa información. Si algún dato no aparece en el Excel, escribe "no indicado".

## Qué produce la app

- Pantalla principal en español con botón para cargar el archivo Excel.
- Tabla que muestra las operaciones por vencer (banco, moneda, monto, días restantes).
- Botón para enviar los avisos por correo al jefe.
- Registro de envíos (archivo de log) con fecha, hora y destinatario.
- Mensaje de aviso en pantalla si hay errores en el archivo (fechas inválidas, filas omitidas).

## Quién decide

El jefe recibe el correo en sandra.jimenez@montecillos.com, revisa la información y toma la decisión final de ejecutar el pago. La app solo avisa; no autoriza ni ejecuta pagos.

## Cifras de control

Con un archivo de prueba que contenga operaciones con vencimiento en 7 días, 1 día, fechas pasadas y fechas futuras (>7 días):
- Debe detectar exactamente las operaciones que faltan 7 días o 1 día para vencer.
- Debe enviar un correo por operación detectada a sandra.jimenez@montecillos.com.
- Debe ignorar operaciones ya vencidas o que vencen en más de 7 días.
- Debe reportar como error las filas con `Próximo Pago` igual a `--/--/----`.
- Debe omitir las filas con `N° Operación` vacío.

## Casos límite

- Archivo Excel vacío: la app avisa del error y no envía correos.
- Fila con `Próximo Pago` igual a `--/--/----`: se reporta como error y no se procesa.
- Fila con `N° Operación` vacío: se omite.
- Símbolo de moneda no reconocido: el agente indica "no indicado" como moneda.
- Archivo no encontrado o dañado: la app muestra un error de lectura en pantalla.
- Dos operaciones con el mismo banco y fecha: se procesan como filas independientes.

## Reglas del sistema

- Lenguaje: Python con Flask.
- Arquitectura: patrón MVC gestionado con `uv`.
- Configuración: la llave del agente de IA se guarda en un archivo `.env` y nunca se escribe dentro del código.
- Inicio: se ejecuta con el archivo `iniciar_app.bat`.
- Interfaz: pantallas sencillas en español.
- Prohibido: inventar reglas o campos que no estén definidos en este documento.
