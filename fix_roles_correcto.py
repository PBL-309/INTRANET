#!/usr/bin/env python3
"""Script para asignar correctamente los roles: 185 BOMBERO, 21 SUBTENIENTE, 8 TENIENTE"""

import sqlite3

conn = sqlite3.connect('/home/sgcpbl/INTRANET/intranet.db')
cursor = conn.cursor()

# IDs correctos
subtenientes_ids = [9, 72, 75, 93, 100, 105, 122, 149, 153, 155, 171, 177, 187, 192, 194, 221, 248, 266, 328, 334, 368]
tenientes_ids = [14, 21, 85, 89, 103, 108, 112, 135]

print("Estado ANTES de cambios:")
cursor.execute("SELECT puesto, COUNT(*) FROM user WHERE puesto IS NOT NULL GROUP BY puesto ORDER BY puesto")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

print(f"\nExpectativa:")
print(f"  BOMBERO ESPECIALIZADO: 185")
print(f"  SUBTENIENTE: {len(subtenientes_ids)}")
print(f"  TENIENTE: {len(tenientes_ids)}")

# Primero establecer todos los que NO sean COORDINADOR ni BOMBERO ESPECIALIZADO (OP. AMB) como BOMBERO ESPECIALIZADO
cursor.execute("""
    UPDATE user 
    SET puesto = 'BOMBERO ESPECIALIZADO' 
    WHERE puesto NOT IN ('COORDINADOR OPERATIVO', 'BOMBERO ESPECIALIZADO (OP. AMB)')
    AND puesto IS NOT NULL
""")
cambios1 = cursor.rowcount
print(f"\n✅ Reiniciados {cambios1} usuarios a BOMBERO ESPECIALIZADO")

# Cambiar SUBTENIENTES exactamente
if subtenientes_ids:
    placeholders = ','.join('?' * len(subtenientes_ids))
    cursor.execute(f"UPDATE user SET puesto = 'SUBTENIENTE' WHERE id IN ({placeholders})", subtenientes_ids)
    cambios_sub = cursor.rowcount
    print(f"✅ Actualizados {cambios_sub} como SUBTENIENTE")

# Cambiar TENIENTES exactamente
if tenientes_ids:
    placeholders = ','.join('?' * len(tenientes_ids))
    cursor.execute(f"UPDATE user SET puesto = 'TENIENTE' WHERE id IN ({placeholders})", tenientes_ids)
    cambios_ten = cursor.rowcount
    print(f"✅ Actualizados {cambios_ten} como TENIENTE")

conn.commit()

print("\nEstado DESPUÉS de cambios:")
cursor.execute("SELECT puesto, COUNT(*) FROM user WHERE puesto IS NOT NULL GROUP BY puesto ORDER BY puesto")
before_dict = {}
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")
    before_dict[row[0]] = row[1]

# Verificar que las evaluaciones se mantienen
cursor.execute("SELECT COUNT(*) FROM evaluacion_desempeno")
total_eval = cursor.fetchone()[0]
print(f"\n✅ Total de evaluaciones preservadas: {total_eval}")

cursor.execute("SELECT puesto, COUNT(*) FROM evaluacion_desempeno GROUP BY puesto")
print("Distribución de evaluaciones:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
