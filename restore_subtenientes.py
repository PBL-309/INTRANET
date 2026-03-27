#!/usr/bin/env python3
"""Script para restaurar SUBTENIENTES y dejar solo TENIENTES"""

import sqlite3

conn = sqlite3.connect('/home/sgcpbl/INTRANET/intranet.db')
cursor = conn.cursor()

# Primero, restaurar SUBTENIENTES
# Necesitamos encontrar quiénes eran SUBTENIENTES antes
# Vamos a usar heurística: si tienen evaluaciones de TENIENTE, eran SUBTENIENTES
# O podemos usar otro criterio

# Ver la situación actual
cursor.execute("SELECT puesto, COUNT(*) FROM user GROUP BY puesto")
print("Estado actual antes de restauración:")
for row in cursor.fetchall():
    if row[0]:
        print(f"  {row[0]}: {row[1]}")

# Contar cuántos fueron convertidos incorrectamente
# Los SUBTENIENTE originales eran 21, ahora hay 29 TENIENTE
# Significa que 8 eran realmente TENIENTE (6 + 1 + 1 anteriormente)
# Pero tenemos 29, lo que significa que se incluyeron los 21 SUBTENIENTE

# Necesitamos restaurar basándonos en evaluaciones o algún otro patrón
# Verificar cuáles tienen evaluaciones como evaluadores
cursor.execute("""
    SELECT DISTINCT u.id, u.nombre 
    FROM user u 
    WHERE u.puesto = 'TENIENTE' 
    AND u.id IN (SELECT evaluador_id FROM evaluacion_desempeno WHERE puesto LIKE 'BOMBERO%')
    LIMIT 50
""")
print("\nTENIENTES que evaluaron BOMBEROS (estos deberían ser SUBTENIENTES):")
subtenientes_ids = []
for row in cursor.fetchall():
    print(f"  ID {row[0]}: {row[1]}")
    subtenientes_ids.append(row[0])

if subtenientes_ids:
    # Restaurar estos como SUBTENIENTE
    placeholders = ','.join('?' * len(subtenientes_ids))
    cursor.execute(f"UPDATE user SET puesto = 'SUBTENIENTE' WHERE id IN ({placeholders})", subtenientes_ids)
    conn.commit()
    print(f"\n✅ Restaurados {len(subtenientes_ids)} SUBTENIENTES")

# Ver resultado final
cursor.execute("SELECT puesto, COUNT(*) FROM user GROUP BY puesto")
print("\nEstado FINAL después de restauración:")
for row in cursor.fetchall():
    if row[0]:
        print(f"  {row[0]}: {row[1]}")

conn.close()
