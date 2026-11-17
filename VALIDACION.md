# VALIDACIÓN - Resultado vs Esperado

Este documento registra los resultados de las pruebas ejecutadas con `pytest`
contra las cifras de control y casos límite definidos en `AGENTS.md`.

## Configuración de pruebas

- Framework: `pytest`
- Archivo de pruebas: `tests/test_servicios.py`
- Archivo de configuración: `tests/conftest.py`
- Comando de ejecución: `pytest` desde la raíz del proyecto

## Cifras de control validadas

| Caso de prueba | Esperado | Obtenido | Estado |
|----------------|----------|----------|--------|
| R1: Archivo Excel inexistente devuelve lista vacía | `[]` | `[]` | ✅ |
| R2: Banco de sección asignado a operación | "Banco X" | "Banco X" | ✅ |
| R3: Fecha en 7 días devuelve 7 días restantes | 7 | 7 | ✅ |
| R3: Fecha en 1 día devuelve 1 día restante | 1 | 1 | ✅ |
| R4: Solo 7 días y 1 día pasan el filtro | 2 operaciones | 2 operaciones | ✅ |
| R9: Vencidos (0 días) e >7 días son ignorados | 0 en resultado | 0 en resultado | ✅ |
| R5: Monto "$1,500.00" se extrae como 1500.0 | 1500.0 | 1500.0 | ✅ |
| R6: Símbolo "$" indica "dólares" | "dólares" | "dólares" | ✅ |
| R6: Sin símbolo "$" indica "colones" | "colones" | "colones" | ✅ |
| R7: Fecha "--/--/----" va a errores | 1 error | 1 error | ✅ |
| R8: N° Operación vacío se omite | 1 operación | 1 operación | ✅ |

## Casos límite validados

| Caso límite | Esperado | Obtenido | Estado |
|-------------|----------|----------|--------|
| Archivo vacío o no encontrado | Lista vacía, sin error crítico | Lista vacía | ✅ |
| Fecha inválida `--/--/----` | Reportada como error, no procesada | En errores | ✅ |
| N° Operación vacío | Fila omitida | Fila omitida | ✅ |
| Moneda sin símbolo reconocida | "colones" | "colones" | ✅ |

## Notas

- Las pruebas se ejecutan con datos sintéticos, no con el archivo real de insumos.
- Para validar con el archivo real `Insumos\LISTA DE OPERACIONES2.xlsx`, ejecutar la app y cargar el archivo manualmente.
- El envío de correo real (SMTP) requiere credenciales configuradas en `.env` (pendiente de confirmar por el usuario).
