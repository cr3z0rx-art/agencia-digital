@echo off
title MultiVenza — Servidor + Ngrok
color 0A
cls

echo.
echo  ============================================================
echo   MultiVenza Digital — Servidor de Automatizacion
echo  ============================================================
echo.

:: Verificar que existe el .env
if not exist "%~dp0.env" (
    echo  ERROR: No se encontro el archivo .env
    echo  Crea el archivo .env en la raiz del proyecto
    pause
    exit /b 1
)

:: Cargar NGROK_DOMAIN del .env
for /f "tokens=1,2 delims==" %%a in (%~dp0.env) do (
    if "%%a"=="NGROK_DOMAIN" set NGROK_DOMAIN=%%b
    if "%%a"=="NGROK_AUTHTOKEN" set NGROK_AUTHTOKEN=%%b
)

if "%NGROK_DOMAIN%"=="" (
    echo  ERROR: Falta NGROK_DOMAIN en el archivo .env
    echo  Ejemplo: NGROK_DOMAIN=tu-nombre.ngrok-free.app
    pause
    exit /b 1
)

echo  Dominio publico : https://%NGROK_DOMAIN%
echo  Webhook URL     : https://%NGROK_DOMAIN%/web-lead-trigger
echo.
echo  Levantando servidor Python...
echo  ============================================================
echo.

:: Abrir ngrok en ventana separada
start "Ngrok Tunnel" cmd /k "ngrok http --domain=%NGROK_DOMAIN% 5050"

:: Esperar 3 segundos para que ngrok arranque
timeout /t 3 /nobreak >nul

:: Levantar el servidor Python en esta ventana
cd /d "%~dp0"
python ghl-integration/webhook_server.py

pause
