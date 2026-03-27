#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('/home/sgcpbl/INTRANET/intranet.db')
cursor = conn.cursor()

# Contar por rol
cursor.execute("SELECT puesto, COUNT(*) FROM user WHERE puesto IS NOT NULL GROUP BY puesto ORDER BY puesto")
print("DISTRIBUCIÓN DE ROLES ACTUAL:\n")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Listar TENIENTES
cursor.execute("SELECT id, username, nombre FROM user WHERE puesto = 'TENIENTE' ORDER BY id")
tenientes = cursor.fetchall()
print(f"\n\nTENIENTES ({len(tenientes)}):")
print('-' * 100)
for row in tenientes:
    print(f"  ID {row[0]:3} | {row[1]:20} | {row[2]}")

# Listar SUBTENIENTES
cursor.execute("SELECT id, username, nombre FROM user WHERE puesto = 'SUBTENIENTE' ORDER BY id")
subtenientes = cursor.fetchall()
print(f"\n\nSUBTENIENTES ({len(subtenientes)}):")
print('-' * 100)
for row in subtenientes:
    print(f"  ID {row[0]:3} | {row[1]:20} | {row[2]}")

conn.close()
