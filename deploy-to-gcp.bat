@echo off
REM Script de despliegue automatizado para INTRANET
REM Uso: deploy-to-gcp.bat "Mensaje del commit"

setlocal enabledelayedexpansion

set "message=%~1"
if "!message!"=="" set "message=Actualizar cambios en producción"

echo.
echo ===============================================
echo INTRANET - Deploy Automatizado a Google Cloud
echo ===============================================
echo.

REM 1. Git add y commit
echo [1/4] Agregando cambios a git...
git add .
git commit -m "!message!"

if errorlevel 1 (
    echo Error en git commit
    exit /b 1
)

REM 2. Git push a GitHub
echo.
echo [2/4] Enviando cambios a GitHub...
git push origin main

if errorlevel 1 (
    echo Error en git push
    exit /b 1
)

echo [✓] Push a GitHub exitoso

REM 3. Crear y copiar script de despliegue
echo.
echo [3/4] Preparando despliegue en Google Cloud...

(
echo #!/bin/bash
echo cd /home/sgcpbl/INTRANET
echo git fetch origin
echo git reset --hard origin/main
echo echo "Cambios sincronizados"
echo pkill -f "gunicorn"
echo sleep 1
echo nohup /home/sgcpbl/INTRANET/venv/bin/gunicorn -w 4 -b 0.0.0.0:5001 main:app ^> /home/sgcpbl/gunicorn.log 2^>^&1 ^&
echo sleep 2
echo echo "Gunicorn reiniciado"
echo curl -s http://localhost:5001/ ^> /dev/null ^&^& echo "Servidor disponible en 5001"
) > remote_deploy.sh

echo  - Copiando script a GCP...
gcloud compute scp remote_deploy.sh instance-20250516-144728:/tmp/deploy.sh --zone=us-central1-c >nul 2>&1

REM 4. Ejecutar despliegue
echo.
echo [4/4] Ejecutando despliegue en Google Cloud...

gcloud compute ssh instance-20250516-144728 --zone=us-central1-c --command "chmod +x /tmp/deploy.sh && sudo -u sgcpbl /tmp/deploy.sh"

if errorlevel 1 (
    echo.
    echo [✗] Error durante despliegue en GCP
    del /q remote_deploy.sh
    exit /b 1
)

echo.
echo ===============================================
echo [✓] Despliegue completado exitosamente
echo Cambios en vivo en: 34.170.131.204:5001
echo ===============================================

del /q remote_deploy.sh
endlocal
