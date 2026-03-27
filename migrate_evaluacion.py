#!/usr/bin/env python
"""
Script de migración manual para agregar el campo evaluador_id a EvaluacionDesempeno
Ejecutar con: python migrate_evaluacion.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import text, inspect

def migrate():
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Verificar si la tabla existe
        if 'evaluacion_desempeno' not in inspector.get_table_names():
            print("❌ La tabla 'evaluacion_desempeno' no existe")
            return False
        
        # Obtener las columnas existentes
        columns = [column['name'] for column in inspector.get_columns('evaluacion_desempeno')]
        
        # Verificar si evaluador_id ya existe
        if 'evaluador_id' in columns:
            print("✓ El campo 'evaluador_id' ya existe en la tabla")
            return True
        
        try:
            # Obtener el tipo de base de datos
            db_url = str(db.engine.url)
            
            if 'sqlite' in db_url:
                print("📝 Detectado SQLite - ejecutando migración...")
                
                # Para SQLite, necesitamos hacer esto de forma diferente
                # SQLite no soporta ALTER TABLE ADD COLUMN con FOREIGN KEY directamente
                # Vamos a crear una nueva tabla y copiar los datos
                
                # Primero, verificar si hay datos
                result = db.session.execute(text("SELECT COUNT(*) FROM evaluacion_desempeno"))
                count = result.scalar()
                print(f"   Registros actuales: {count}")
                
                # Crear tabla temporal con la nueva estructura
                db.session.execute(text("""
                    CREATE TABLE evaluacion_desempeno_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        evaluador_id INTEGER NOT NULL DEFAULT 1,
                        nombre VARCHAR(100) NOT NULL,
                        fecha DATE NOT NULL,
                        area VARCHAR(100) NOT NULL,
                        estacion VARCHAR(100) NOT NULL,
                        nomina VARCHAR(20) NOT NULL,
                        puesto VARCHAR(100) NOT NULL,
                        respuestas JSON NOT NULL,
                        evaluacion_general VARCHAR(20) NOT NULL,
                        comentario VARCHAR(500),
                        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES user(id),
                        FOREIGN KEY(evaluador_id) REFERENCES user(id)
                    )
                """))
                
                # Copiar datos (asignando evaluador_id = user_id por defecto, o 1 si no existe)
                db.session.execute(text("""
                    INSERT INTO evaluacion_desempeno_new
                    SELECT id, user_id, 1, nombre, fecha, area, estacion, nomina, puesto,
                           respuestas, evaluacion_general, comentario, fecha_creacion
                    FROM evaluacion_desempeno
                """))
                
                # Eliminar tabla antigua
                db.session.execute(text("DROP TABLE evaluacion_desempeno"))
                
                # Renombrar tabla nueva
                db.session.execute(text("ALTER TABLE evaluacion_desempeno_new RENAME TO evaluacion_desempeno"))
                
                db.session.commit()
                print("✓ Migración completada exitosamente para SQLite")
                return True
                
            elif 'postgresql' in db_url or 'mysql' in db_url:
                print("📝 Detectado PostgreSQL/MySQL - ejecutando migración...")
                
                # Para PostgreSQL y MySQL, es más directo
                db.session.execute(text("""
                    ALTER TABLE evaluacion_desempeno 
                    ADD COLUMN evaluador_id INTEGER NOT NULL DEFAULT 1,
                    ADD FOREIGN KEY (evaluador_id) REFERENCES user(id)
                """))
                
                db.session.commit()
                print("✓ Migración completada exitosamente para PostgreSQL/MySQL")
                return True
            else:
                print(f"❌ Base de datos no soportada: {db_url}")
                return False
                
        except Exception as e:
            print(f"❌ Error durante la migración: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
