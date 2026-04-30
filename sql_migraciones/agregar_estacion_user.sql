-- Migración: Agregar columna 'estacion' a la tabla 'user'
-- Fecha: 2026-04-30
-- Descripción: Agrega la columna estacion para almacenar la estación asignada a cada usuario

ALTER TABLE user ADD COLUMN estacion VARCHAR(50);

-- Opcional: Si necesitas establecer un valor por defecto para registros existentes
-- UPDATE user SET estacion = 'Estación Central' WHERE estacion IS NULL;
