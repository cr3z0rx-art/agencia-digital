@echo off
setlocal enabledelayedexpansion
title MultiVenza Digital — Panel de Control
color 0B
cd /d "%~dp0"

:MENU
cls
echo.
echo  [34m============================================================[0m
echo.
echo        [1m[36mM U L T I V E N Z A   D I G I T A L[0m
echo          [90mPanel de Control — Mando a Distancia[0m
echo.
echo  [34m============================================================[0m
echo.
echo   [33m[1][0m  Limpieza Total      — Cerrar todos los servidores viejos
echo   [33m[2][0m  Encender Sistema    — Lanzar Flask + Ngrok
echo   [33m[3][0m  Envio Masivo        — Enviar emails a leads pendientes
echo   [33m[4][0m  Ver Logs            — Monitorear actividad en tiempo real
echo   [33m[5][0m  Estado de GHL       — Ver leads nuevos en el Pipeline
echo   [33m[0][0m  Salir
echo.
echo  [34m============================================================[0m
echo.
set /p OPCION=   Elige una opcion [0-5]:

if "%OPCION%"=="1" goto LIMPIEZA
if "%OPCION%"=="2" goto ENCENDER
if "%OPCION%"=="3" goto EMAILS
if "%OPCION%"=="4" goto LOGS
if "%OPCION%"=="5" goto GHL_STATUS
if "%OPCION%"=="0" goto SALIR
goto MENU


:: ─────────────────────────────────────────────────────────
:LIMPIEZA
cls
echo.
echo  [31m============================================================[0m
echo   [1m[31m LIMPIEZA TOTAL[0m — Cerrando procesos viejos...
echo  [31m============================================================[0m
echo.

taskkill /F /IM python.exe >nul 2>&1
if %ERRORLEVEL%==0 (
    echo   [32mOK[0m  Procesos Python cerrados
) else (
    echo   [90mINFO[0m No habia procesos Python corriendo
)

taskkill /F /IM ngrok.exe >nul 2>&1
if %ERRORLEVEL%==0 (
    echo   [32mOK[0m  Proceso Ngrok cerrado
) else (
    echo   [90mINFO[0m No habia Ngrok corriendo
)

echo.
echo   [32mSistema limpio — listo para encender.[0m
echo.
pause
goto MENU


:: ─────────────────────────────────────────────────────────
:ENCENDER
cls
echo.
echo  [32m============================================================[0m
echo   [1m[32m ENCENDER SISTEMA[0m — Lanzando Flask + Ngrok...
echo  [32m============================================================[0m
echo.
echo   Abriendo servidor en ventana separada...
echo.
start "MultiVenza — Servidor + Ngrok" cmd /k "cd /d %~dp0 && call start-server.bat"
echo   [32mOK[0m  Servidor lanzado. Revisa la ventana nueva.
echo.
echo   URL Webhook: https://tu-dominio.ngrok-free.app/web-lead-trigger
echo   URL Flask:   http://localhost:5050
echo.
pause
goto MENU


:: ─────────────────────────────────────────────────────────
:EMAILS
cls
echo.
echo  [36m============================================================[0m
echo   [1m[36m ENVIO MASIVO[0m — Campana de email outreach
echo  [36m============================================================[0m
echo.

:: Contar pendientes antes de enviar
python -c "
import csv
try:
    with open('leads/leads_with_emails.csv', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    pending = [r for r in rows if r.get('contacted','').strip() == 'NO' and r.get('email','').strip() not in ('','NO EMAIL','N/A','nan')]
    total   = len(rows)
    sent    = sum(1 for r in rows if r.get('contacted','').strip() == 'YES')
    print(f'  Total leads:     {total}')
    print(f'  Ya contactados:  {sent}')
    print(f'  Pendientes:      {len(pending)}')
except Exception as e:
    print(f'  Error leyendo CSV: {e}')
" 2>nul

echo.
set /p CONFIRMAR=   Enviar emails a todos los pendientes? [S/N]:
if /i "%CONFIRMAR%"=="S" (
    echo.
    echo   Iniciando envio... [Ctrl+C para detener]
    echo.
    python ghl-integration/send_emails.py
    echo.
    echo   [32mEnvio completado.[0m Revisa logs/send_emails.log para el resumen.
) else (
    echo.
    echo   Cancelado.
)
echo.
pause
goto MENU


:: ─────────────────────────────────────────────────────────
:LOGS
cls
echo.
echo  [35m============================================================[0m
echo   [1m[35m VER LOGS[0m — Monitoreo en tiempo real
echo  [35m============================================================[0m
echo.
echo   Elige que log ver:
echo.
echo   [33m[1][0m  Emails enviados     (send_emails.log)
echo   [33m[2][0m  Servidor / Webhooks (webhook_server.log)
echo   [33m[3][0m  Subida a GHL        (ghl_upload_log.csv)
echo   [33m[4][0m  Volver al menu
echo.
set /p LOG_OP=   Opcion:

if "%LOG_OP%"=="1" (
    start "Logs — Emails" powershell -NoExit -Command "Get-Content 'logs\send_emails.log' -Wait -Tail 20"
)
if "%LOG_OP%"=="2" (
    if exist "logs\webhook_server.log" (
        start "Logs — Servidor" powershell -NoExit -Command "Get-Content 'logs\webhook_server.log' -Wait -Tail 20"
    ) else (
        echo   El log del servidor se muestra directamente en la ventana de Flask.
        pause
    )
)
if "%LOG_OP%"=="3" (
    start "Logs — GHL Upload" powershell -NoExit -Command "Get-Content 'logs\ghl_upload_log.csv' -Wait -Tail 20"
)
goto MENU


:: ─────────────────────────────────────────────────────────
:GHL_STATUS
cls
echo.
echo  [33m============================================================[0m
echo   [1m[33m ESTADO DE GHL[0m — Pipeline: Contratistas Latinos
echo  [33m============================================================[0m
echo.
echo   Consultando GHL...
echo.

python -c "
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path('ghl-integration').resolve()))
from dotenv import load_dotenv
load_dotenv('.env')

try:
    from ghl_client import get_pipeline_by_name, _headers, BASE_URL
    import requests

    pipeline = get_pipeline_by_name('Contratistas Latinos')
    if not pipeline:
        print('  ERROR: Pipeline no encontrado en GHL')
        sys.exit(1)

    pipeline_id = pipeline.get('id')
    stages = {s['name']: s['id'] for s in pipeline.get('stages', [])}

    r = requests.get(
        f'{BASE_URL}/opportunities/search',
        headers=_headers(),
        params={'pipeline_id': pipeline_id, 'limit': 100}
    )
    if not r.ok:
        print(f'  ERROR consultando GHL: {r.status_code}')
        sys.exit(1)

    opps = r.json().get('opportunities', [])
    from collections import Counter
    by_stage = Counter(o.get('pipelineStageId','') for o in opps)
    stage_names = {v: k for k, v in stages.items()}

    total = len(opps)
    print(f'  Total oportunidades: {total}')
    print()
    for stage_id, count in by_stage.most_common():
        name = stage_names.get(stage_id, stage_id[:12])
        bar = '#' * min(count, 30)
        print(f'  {name:<25} {count:>4}  {bar}')

    open_count = sum(1 for o in opps if o.get('status') == 'open')
    won_count  = sum(1 for o in opps if o.get('status') == 'won')
    print()
    print(f'  Abiertas:  {open_count}')
    print(f'  Cerradas (won): {won_count}')

except Exception as e:
    print(f'  Error: {e}')
" 2>nul

echo.
pause
goto MENU


:: ─────────────────────────────────────────────────────────
:SALIR
cls
echo.
echo  [90m  Cerrando panel... Hasta luego.[0m
echo.
exit /b 0
