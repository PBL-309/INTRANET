#!/usr/bin/env python
"""
Script para probar el filtrado por turno en resultados_evaluaciones.
Ejecuta esto después de la próxima vez que veas el problema.
"""

from app import db, create_app
from app.models import User, EvaluacionDesempeno
import sys

app = create_app()
app.app_context().push()

def test_turno_filter(rol='BOMBERO ESPECIALIZADO'):
    print(f"\n{'='*60}")
    print(f"Testing filtrado para ROL: {rol}")
    print(f"{'='*60}\n")
    
    # Test GENERAL
    print("1. FILTRANDO GENERAL (todos los usuarios del rol):")
    usuarios_general = User.query.filter_by(puesto=rol).all()
    print(f"   Total usuarios {rol}: {len(usuarios_general)}")
    
    if usuarios_general:
        print(f"   Distribución de turnos:")
        turnos_dist = {}
        for u in usuarios_general:
            turno = u.turno or 'NULL'
            turnos_dist[turno] = turnos_dist.get(turno, 0) + 1
        for turno, count in sorted(turnos_dist.items()):
            print(f"     - Turno {turno}: {count} usuarios")
        
        usuario_ids_general = [u.id for u in usuarios_general]
        evals_general = EvaluacionDesempeno.query.filter(
            EvaluacionDesempeno.user_id.in_(usuario_ids_general)
        ).all()
        print(f"   Evaluaciones encontradas: {len(evals_general)}\n")
    
    # Test cada turno específico
    for turno in ['A', 'B', 'C']:
        print(f"2. FILTRANDO TURNO {turno}:")
        usuarios_turno = User.query.filter_by(puesto=rol, turno=turno).all()
        print(f"   Usuarios encontrados: {len(usuarios_turno)}")
        
        if usuarios_turno:
            usuario_ids_turno = [u.id for u in usuarios_turno]
            evals_turno = EvaluacionDesempeno.query.filter(
                EvaluacionDesempeno.user_id.in_(usuario_ids_turno)
            ).all()
            print(f"   Evaluaciones encontradas: {len(evals_turno)}")
        print()

if __name__ == '__main__':
    # Probar todos los roles
    for rol in ['BOMBERO ESPECIALIZADO', 'SUBTENIENTE', 'TENIENTE']:
        test_turno_filter(rol)

print("\n✓ Test completado. Revisa los logs más arriba.")
