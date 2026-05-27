#!/bin/bash
cd /home/sgcpbl/INTRANET
source venv/bin/activate
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/sgcpbl/INTRANET')
from main import db, app
from app.models import User, PermisosEvaluacion

app.app_context().push()

# 1. Limpiar permisos anteriores
PermisosEvaluacion.query.delete()
db.session.commit()
print("✓ Permisos anteriores eliminados")

# 2. Obtener usuarios por puesto exacto
bomberos_especializados = User.query.filter(User.puesto == 'BOMBERO ESPECIALIZADO').all()
bomberos_habilitados = User.query.filter(User.puesto == 'BOMBERO HABILITADO').all()
subtenientes = User.query.filter(User.puesto == 'SUBTENIENTE').all()
tenientes = User.query.filter(User.puesto == 'TENIENTE').all()
coordinadores = User.query.filter(User.puesto == 'COORDINADOR').all()

print(f"\nUsuarios por puesto:")
print(f"  - BOMBERO ESPECIALIZADO: {len(bomberos_especializados)}")
print(f"  - BOMBERO HABILITADO: {len(bomberos_habilitados)}")
print(f"  - SUBTENIENTE: {len(subtenientes)}")
print(f"  - TENIENTE: {len(tenientes)}")
print(f"  - COORDINADOR: {len(coordinadores)}")

# 3. Asignar permisos según roles
count = 0

# SUBTENIENTE + BOMBERO HABILITADO -> BOMBERO ESPECIALIZADO
evaluadores_grupo1 = subtenientes + bomberos_habilitados
for evaluador in evaluadores_grupo1:
    for evaluado in bomberos_especializados:
        if evaluador.id != evaluado.id:
            perm = PermisosEvaluacion(evaluador_id=evaluador.id, evaluado_id=evaluado.id)
            db.session.add(perm)
            count += 1

# TENIENTE -> SUBTENIENTE + BOMBERO HABILITADO
evaluados_grupo2 = subtenientes + bomberos_habilitados
for evaluador in tenientes:
    for evaluado in evaluados_grupo2:
        if evaluador.id != evaluado.id:
            perm = PermisosEvaluacion(evaluador_id=evaluador.id, evaluado_id=evaluado.id)
            db.session.add(perm)
            count += 1

# COORDINADOR -> TENIENTE
for evaluador in coordinadores:
    for evaluado in tenientes:
        if evaluador.id != evaluado.id:
            perm = PermisosEvaluacion(evaluador_id=evaluador.id, evaluado_id=evaluado.id)
            db.session.add(perm)
            count += 1

db.session.commit()

print(f"\n✓ Permisos asignados correctamente:")
print(f"  - SUBTENIENTE + BOMBERO HABILITADO → BOMBERO ESPECIALIZADO")
print(f"  - TENIENTE → SUBTENIENTE + BOMBERO HABILITADO")
print(f"  - COORDINADOR → TENIENTE")
print(f"\n✓ Total de permisos creados: {count}")

EOF
