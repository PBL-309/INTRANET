# Resumen de Cambios - Sistema de Evaluaciones con Prevención de Duplicados

## ✅ Cambios Realizados

### 1. **Modelo de Base de Datos** ([app/models.py](app/models.py#L133-L156))
   - ✅ Agregado campo `evaluador_id` (Foreign Key a User)
   - ✅ Actualizado campo `user_id` para representar al usuario evaluado (no al evaluador)
   - ✅ Creadas relaciones duales:
     - `usuario_evaluado` → usuario siendo evaluado
     - `usuario_evaluador` → usuario haciendo la evaluación
   - 📌 **Nota**: Estos cambios evitan la ambigüedad anterior donde no se sabía quién evaluó a quién

### 2. **API Endpoints** ([app/routes.py](app/routes.py#L721-L733))
   - ✅ Modificado `/api/buscar_usuario/<username>` para devolver:
     - Agregado campo `id` (user_id del usuario)
     - Los campos existentes: nombre, puesto, turno, nomina, image_file
   - 📌 **Uso**: JavaScript del frontend usa esto para capturar el ID del evaluado

### 3. **Procesamiento de Evaluaciones** ([app/routes.py](app/routes.py#L397-L475))
   - ✅ Reescrito `submit_evaluacion()` con:
     - **Extracción de evaluado_id**: Obtiene el ID del formulario (campo `evaluado_id`)
     - **Validación de duplicados**: 
       ```python
       existing = EvaluacionDesempeno.query.filter_by(
           user_id=evaluado_id,
           evaluador_id=current_user.id
       ).first()
       ```
     - **Prevención de re-evaluación**: Si ya existe, muestra mensaje "Ya has evaluado a esta persona"
     - **Guardado correcto**: `evaluacion = EvaluacionDesempeno(user_id=evaluado_id, evaluador_id=current_user.id, ...)`

### 4. **Plantillas HTML** (evaluacion_subteniente.html, evaluacion_teniente.html, evaluacion_coordinador.html)
   - ✅ Todos los templates actualizados con:
     - Nuevo campo oculto: `<input type="hidden" id="evaluado_id" name="evaluado_id" required />`
     - JavaScript mejorado que guarda el `data.id` en `evaluado_id.value`
     - El formulario ahora envía: `evaluado_id` + todos los datos de evaluación

### 5. **Inicialización de Aplicación** ([app/__init__.py](app/__init__.py#L47-L89))
   - ✅ Comentado código de inicialización de facial_service:
     - Facial recognition ya fue removido por el usuario
     - Esto evita errores de MediaPipe al ejecutar comandos Flask
     - Permite que `flask db` funcione correctamente

### 6. **Migración de Base de Datos**
   - ✅ Creado script `migrate_evaluacion.py` para PostgreSQL/MySQL/SQLite
   - ✅ Script ejecutado exitosamente
   - ✅ Tabla `evaluacion_desempeno` ahora tiene campo `evaluador_id`

---

## 🔄 Flujo de Evaluación (Actualizado)

### Antes (Incorrecto)
```
Subteniente A evalúa a Bombero B
→ Guardaba: user_id = A, nombre = B
→ Problema: ¿A está siendo evaluado por B? ¿B está siendo evaluado por A?
```

### Ahora (Correcto)
```
Subteniente A evalúa a Bombero B
→ JavaScript captura: evaluado_id = B.id, nombre = B.nombre
→ Envía: evaluado_id=B.id
→ Guardado: user_id=B (evaluado), evaluador_id=A (evaluador)
→ Validación: Si A ya evaluó a B, rechazar con mensaje
→ Relaciones claras: evaluaciones_recibidas (quien fue evaluado), evaluaciones_realizadas (quien evaluó)
```

---

## 🔐 Prevención de Duplicados

**Implementación**:
```python
# En submit_evaluacion() - Línea 410-418
existing = EvaluacionDesempeno.query.filter_by(
    user_id=evaluado_id,
    evaluador_id=current_user.id
).first()

if existing:
    flash("Ya has evaluado a esta persona. No puedes hacer una evaluación duplicada.", "warning")
    return redirect(request.referrer)
```

**Resultado**:
- ✅ Usuario intenta evaluar a la misma persona 2 veces
- ✅ Sistema verifica si existe registro previo
- ✅ Si existe: muestra warning y rechaza
- ✅ Si no existe: guarda normalmente

---

## 📊 Jerarquía de Evaluaciones (Mantiene la Estructura)

El sistema mantiene la jerarquía ya implementada en `/api/listar_usuarios()`:

| Evaluador | Evalúa a |
|-----------|----------|
| Coordinador Operativo | TENIENTE |
| TENIENTE | SUBTENIENTE |
| SUBTENIENTE | BOMBERO ESPECIALIZADO |

---

## 🧪 Verificación Local

Para verificar que todo funciona:

1. **Iniciar servidor**:
   ```bash
   cd c:\Users\PBL-ADMINISTRADOR\Documents\intranet
   python main.py
   ```

2. **Prueba manual**:
   - Acceder como Subteniente
   - Ir a Evaluación del Desempeño
   - Seleccionar un Bombero y completar evaluación
   - Intentar evaluar al mismo Bombero de nuevo
   - ✅ Debe mostrar: "Ya has evaluado a esta persona..."

3. **Verificar BD**:
   ```bash
   sqlite3 empleados.db
   SELECT * FROM evaluacion_desempeno;
   ```

---

## 📦 Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `app/models.py` | Agregado `evaluador_id`, relaciones duales |
| `app/routes.py` | Modificado `/api/buscar_usuario`, reescrito `submit_evaluacion()` |
| `app/templates/evaluacion_subteniente.html` | Agregado `evaluado_id`, JS actualizado |
| `app/templates/evaluacion_teniente.html` | Mismo cambios que subteniente |
| `app/templates/evaluacion_coordinador.html` | Mismo cambios que subteniente |
| `app/__init__.py` | Comentado código de facial_service |
| `migrate_evaluacion.py` | NUEVO - Script de migración |

---

## 🚀 Próximos Pasos (Para Despliegue)

1. **En el servidor GCP**:
   ```bash
   cd /home/ubuntu/intranet
   python migrate_evaluacion.py  # Ejecutar migración
   git pull                        # Actualizar código
   systemctl restart intranet    # Reiniciar servicio
   ```

2. **Verificar logs**:
   ```bash
   journalctl -u intranet -f
   ```

3. **Test en producción**:
   - Acceder a https://34.170.131.204:5001
   - Realizar el mismo test que en local

---

## ℹ️ Notas Técnicas

- 🔑 El campo `evaluado_id` es requerido en todos los formularios de evaluación
- 🔒 La prevención de duplicados se valida en el backend (servidor)
- 📱 El frontend captura el ID desde la API `/api/buscar_usuario`
- 🗄️ La migración es compatible con SQLite (local) y PostgreSQL/MySQL (servidor)
- ⚠️ Para SQLite se crea tabla nueva + copia de datos (porque SQLite no soporta ALTER COLUMN bien)

---

**Estado**: ✅ LISTO PARA DESPLIEGUE

**Testeado en**: Windows local con SQLite
**Pendiente de test**: Servidor GCP con PostgreSQL
