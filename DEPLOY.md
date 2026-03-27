# Script de Despliegue Automatizado - INTRANET

Este proyecto incluye scripts automatizados para hacer deploy rápide a Google Cloud sin tener que ejecutar comandos manualmente.

## 📋 Opciones disponibles

### Opción 1: Script PowerShell (Recomendado para usuarios avanzados)

**Archivo:** `deploy-to-gcp.ps1`

```powershell
# Con mensaje por defecto
.\deploy-to-gcp.ps1

# Con mensaje personalizado
.\deploy-to-gcp.ps1 -message "Modernizar estilos y agregar nueva funcionalidad"
```

**Nota:** Si PowerShell no permite ejecutar el script, ejecuta primero:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Opción 2: Script Batch (Recomendado para usuarios de Windows)

**Archivo:** `deploy-to-gcp.bat`

Haz doble clic o ejecuta desde cmd:

```cmd
deploy-to-gcp.bat
```

Con mensaje personalizado:
```cmd
deploy-to-gcp.bat "Mi mensaje de commit personalizado"
```

---

## 🔄 Qué hace el script

El script automatiza estos 4 pasos:

1. **Git add & commit** - Agrega todos los cambios locales y crea un commit
2. **Git push** - Envía los cambios a GitHub (rama main)
3. **GCP sync** - Sincroniza el código en Google Cloud usando SSH
4. **Gunicorn restart** - Reinicia el servidor web (4 workers)

```
Tu máquina local  →  GitHub  →  Google Cloud  →  Servidor en vivo
```

---

## 📊 Información del servidor

- **IP pública:** 34.170.131.204
- **Puerto:** 5001
- **Zona GCP:** us-central1-c
- **Instancia:** instance-20250516-144728
- **Usuario GCP:** sgcpbl
- **Ruta proyecto:** /home/sgcpbl/INTRANET
- **Venv:** /home/sgcpbl/INTRANET/venv

---

## ✅ Ejemplo de uso

```bash
# 1. Modifica archivos en tu máquina local
# (ejemplo: cambios en CSS, JavaScript, etc.)

# 2. Ejecuta el deploy
.\deploy-to-gcp.ps1 -message "Mejorar estilos de formularios"

# El script hace automáticamente:
# ✓ git add .
# ✓ git commit -m "Mejorar estilos de formularios"
# ✓ git push origin main
# ✓ Copia script a GCP
# ✓ Ejecuta: git fetch, git reset, pkill gunicorn, reinicia gunicorn
```

---

## 🐛 Solución de problemas

### Error de permisos con PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error de conexión GCP
```bash
# Verifica que gcloud está configurado
gcloud auth list
gcloud config get-value project
```

### Ver logs en servidor remoto
```bash
gcloud compute ssh instance-20250516-144728 --zone=us-central1-c --command "tail -f /home/sgcpbl/gunicorn.log"
```

### Verificar estado del servidor
```bash
gcloud compute ssh instance-20250516-144728 --zone=us-central1-c --command "ps aux | grep gunicorn"
```

---

## 📝 Notas

- Los scripts requieren tener `gcloud CLI` instalado y configurado
- Debes estar dentro del directorio del proyecto cuando ejecutes los scripts
- Los cambios se envían a la rama `main` automáticamente
- El servidor en Google Cloud se actualiza en tiempo real

---

**Último deploy:** 2026-03-27  
**Commit:** 34f63c4  
**URL en vivo:** http://34.170.131.204:5001

