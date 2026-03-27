#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('/home/sgcpbl/INTRANET/intranet.db')
cursor = conn.cursor()

cursor.execute("SELECT id, username, nombre, puesto FROM user WHERE puesto = 'TENIENTE' ORDER BY id")
tenientes = cursor.fetchall()

print(f'Total de TENIENTES: {len(tenientes)}\n')
print('ID | Username | Nombre | Puesto')
print('-' * 100)
for row in tenientes:
    print(f'{row[0]:3} | {row[1]:20} | {row[2]:40} | {row[3]}')

conn.close()
