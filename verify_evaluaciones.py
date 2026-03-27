#!/usr/bin/env python3
"""Script para verificar que las evaluaciones se pueden consultar correctamente"""

import sqlite3
import json

conn = sqlite3.connect('/home/sgcpbl/INTRANET/intranet.db')
cursor = conn.cursor()

# Verificar usuarios BOMBERO
cursor.execute("SELECT id, nombre, puesto FROM user WHERE puesto LIKE 'BOMBERO%'")
usuarios_bombero = cursor.fetchall()
print(f"Total de BOMBERO ESPECIALIZADO: {len(usuarios_bombero)}")

# Obtener IDs
bombero_ids = [u[0] for u in usuarios_bombero]

# Obtener evaluaciones de bomberos
if bombero_ids:
    placeholders = ','.join('?' * len(bombero_ids))
    cursor.execute(f"SELECT id, user_id, puesto, estacion, respuestas FROM evaluacion_desempeno WHERE user_id IN ({placeholders}) LIMIT 5", bombero_ids)
    evaluaciones = cursor.fetchall()
    print(f"Total de evaluaciones de BOMBERO: {len(evaluaciones)}")
    
    # Verificar estructura de respuestas
    if evaluaciones:
        eval_id, user_id, puesto, estacion, respuestas_json = evaluaciones[0]
        print(f"\nPrimer evaluación:")
        print(f"  ID: {eval_id}")
        print(f"  Usuario: {user_id}")
        print(f"  Puesto: {puesto}")
        print(f"  Estación (Turno): {estacion}")
        
        try:
            respuestas = json.loads(respuestas_json)
            print(f"  Categorías en respuestas: {list(respuestas.keys())}")
            if 'comunicacion' in respuestas:
                print(f"    Subcategorías de comunicación: {list(respuestas['comunicacion'].keys())}")
        except json.JSONDecodeError as e:
            print(f"  Error al parsear JSON: {e}")

conn.close()
