# Script de despliegue automatizado para INTRANET
# Función: Commit, push a GitHub, y actualizar Google Cloud

param(
    [string]$message = "Actualizar cambios en producción"
)

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "INTRANET - Deploy Automatizado a Google Cloud" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# Variables de configuración
$projectRoot = Split-Path -Parent $MyInvocation.MyCommandPath
$gcpzone = "us-central1-c"
$gcpinstance = "instance-20250516-144728"
$gcpuser = "sgcpbl"
$intranetPath = "/home/sgcpbl/INTRANET"

# Cambiar al directorio del proyecto
Set-Location $projectRoot

# 1. Git add y commit
Write-Host "`n[1/4] Agregando cambios a git..." -ForegroundColor Yellow
git add .
git commit -m "$message"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error en git commit" -ForegroundColor Red
    exit 1
}

# 2. Git push a GitHub
Write-Host "`n[2/4] Enviando cambios a GitHub..." -ForegroundColor Yellow
git push origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error en git push" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Push a GitHub exitoso" -ForegroundColor Green

# 3. Crear script de despliegue remoto
Write-Host "`n[3/4] Preparando despliegue en Google Cloud..." -ForegroundColor Yellow

$deployScript = @"
#!/bin/bash
cd $intranetPath
git fetch origin
git reset --hard origin/main
echo "Cambios sincronizados"
pkill -f "gunicorn"
sleep 1
nohup $intranetPath/venv/bin/gunicorn -w 4 -b 0.0.0.0:5001 main:app > /home/sgcpbl/gunicorn.log 2>&1 &
sleep 2
echo "Gunicorn reiniciado"
curl -s http://localhost:5001/ > /dev/null && echo "Servidor disponible en 5001"
"@

# Guardar script temporalmente
$deployScript | Out-File -FilePath "$projectRoot\remote_deploy.sh" -Encoding ASCII

# Copiar a Google Cloud
Write-Host "  - Copiando script a GCP..." -ForegroundColor Gray
gcloud compute scp "$projectRoot\remote_deploy.sh" "${gcpinstance}:/tmp/deploy.sh" --zone=$gcpzone 2>&1 | Out-Null

# 4. Ejecutar script en Google Cloud
Write-Host "`n[4/4] Ejecutando despliegue en Google Cloud..." -ForegroundColor Yellow

gcloud compute ssh $gcpinstance --zone=$gcpzone --command "chmod +x /tmp/deploy.sh && sudo -u $gcpuser /tmp/deploy.sh"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Despliegue completado exitosamente" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host "Cambios en vivo en: 34.170.131.204:5001" -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Green
    
    # Limpiar script temporal
    Remove-Item "$projectRoot\remote_deploy.sh" -Force
} else {
    Write-Host "`n✗ Error durante despliegue en GCP" -ForegroundColor Red
}
