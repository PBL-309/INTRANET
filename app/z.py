import pandas as pd

# Cargar tu archivo Excel
ruta_excel = "salida.xlsx"  # Cambia si tiene otro nombre
df = pd.read_excel(ruta_excel)

# Inicializar lista de sentencias
sentencias_sql = []
contador_id = 1

for _, row in df.iterrows():
    user_id = int(row['user_id'])
    correo = row['correo'].strip()

    nombre_acompanante = row.get('nombre_acompanante')
    tipo_acompanante = row.get('tipo_acompanante')

    # Manejo de valores nulos
    nombre_acompanante = f"'{nombre_acompanante.strip()}'" if pd.notna(nombre_acompanante) and str(nombre_acompanante).strip() != "" else "NULL"
    tipo_acompanante = f"'{tipo_acompanante.strip()}'" if pd.notna(tipo_acompanante) and str(tipo_acompanante).strip() != "" else "NULL"

    correo = f"'{correo}'"

    respondido = 1
    asistio = 0

    sql = f"INSERT INTO respuesta (id, user_id, nombre_acompanante, correo, respondido, asistio, tipo_acompanante) VALUES ({contador_id}, {user_id}, {nombre_acompanante}, {correo}, {respondido}, {asistio}, {tipo_acompanante});"
    sentencias_sql.append(sql)
    contador_id += 1

# Guardar archivo .sql
with open("insert_respuestas.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(sentencias_sql))

print("✅ Archivo 'insert_respuestas.sql' generado.")
