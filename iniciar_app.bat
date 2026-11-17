@echo off
cd /d "%~dp0"

echo Iniciando entorno uv...
uv run flask --app wsgi run --host=127.0.0.1 --port=5000 > flask.log 2>&1 &

echo Esperando a que la app inicie...
timeout /t 3 >nul

echo Abriendo navegador en http://127.0.0.1:5000
start http://127.0.0.1:5000

echo App ejecutándose. Presione cualquier tecla para cerrar.
pause >nul
