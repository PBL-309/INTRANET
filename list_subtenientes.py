#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('/home/sgcpbl/INTRANET/intranet.db')
cursor = conn.cursor()

cursor.execute("SELECT id, username, nombre, puesto FROM user WHERE puesto = 'SUBTENIENTE' ORDER BY id")
subtenientes = cursor.fetchall()

print(f'Total de SUBTENIENTES: {len(subtenientes)}\n')
print('ID | Username | Nombre | Puesto')
print('-' * 100)
for row in subtenientes:
    print(f'{row[0]:3} | {row[1]:20} | {row[2]:40} | {row[3]}')

conn.close()
