#!/bin/bash
cd /home/sgcpbl/INTRANET
source venv/bin/activate
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/sgcpbl/INTRANET')
from main import db, app
from app.models import User, PermisosEvaluacion

app.app_context().push()

# 1. Eliminar todos los permisos de evaluadores que sean bomberos
bomberos = User.query.filter(User.puesto.ilike('%bombero%')).all()
bombero_ids = [b.id for b in bomberos]

if bombero_ids:
    PermisosEvaluacion.query.filter(PermisosEvaluacion.evaluador_id.in_(bombero_ids)).delete()
    db.session.commit()
    print(f"✓ Eliminados permisos de {len(bombero_ids)} bomberos como evaluadores")

# 2. Obtener usuarios por rol
subtenientes = User.query.filter(User.puesto.ilike('%subteniente%')).all()
bomberos_habilitados = User.query.filter(User.puesto.ilike('%bombero especializado%')).all()
tenientes = User.query.filter(User.puesto.ilike('%teniente%')).all()
coordinadores = User.query.filter(User.puesto.ilike('%coordinador%')).all()

# 3. Asignar permisos por rol
assignments = []

# Subtenientes y Bomberos Habilitados -> evalúan a Bomberos
evaluadores_bomberos = subtenientes + bomberos_habilitados
bomberos_simples = User.query.filter(
    User.puesto.ilike('%bombero%'),
    ~User.puesto.ilike('%especializado%'),
    ~User.puesto.ilike('%subteniente%')
).all()

for evaluador in evaluadores_bomberos:
    for bombero in bomberos_simples:
        if evaluador.id != bombero.id:  # No evaluarse a sí mismo
            perm = PermisosEvaluacion(evaluador_id=evaluador.id, evaluado_id=bombero.id)
            db.session.merge(perm)
            assignments.append(f"  {evaluador.nombre} ({evaluador.puesto}) -> {bombero.nombre} (bombero)")

# Tenientes -> evalúan a Subtenientes
for teniente in tenientes:
    for subteniente in subtenientes:
        if teniente.id != subteniente.id:
            perm = PermisosEvaluacion(evaluador_id=teniente.id, evaluado_id=subteniente.id)
            db.session.merge(perm)
            assignments.append(f"  {teniente.nombre} (teniente) -> {subteniente.nombre} (subteniente)")

# Coordinadores -> evalúan a Tenientes
for coordinador in coordinadores:
    for teniente in tenientes:
        if coordinador.id != teniente.id:
            perm = PermisosEvaluacion(evaluador_id=coordinador.id, evaluado_id=teniente.id)
            db.session.merge(perm)
            assignments.append(f"  {coordinador.nombre} (coordinador) -> {teniente.nombre} (teniente)")

db.session.commit()

print(f"\n✓ Permisos asignados:")
print(f"  - Subtenientes + Bomberos Habilitados -> Bomberos")
print(f"  - Tenientes -> Subtenientes")
print(f"  - Coordinadores -> Tenientes")
print(f"\n✓ Total de asignaciones: {len(assignments)}")

EOF
