-- =====================================================================
-- Migración 002: cambio de contraseña obligatorio (paso 0.3)
--
-- Agrega usuario.debe_cambiar_clave. Cuando un Administrador o un Jefe de
-- área crea un usuario o le restablece la contraseña, el sistema le da
-- una clave temporal y pone esta columna en 1. Mientras esté en 1, el
-- usuario no puede usar el sistema hasta elegir su propia contraseña.
--
-- Para quién: bases creadas antes del paso 0.3. Una base nueva creada con
-- el der_v3.sql actual ya la tiene.
--
-- Cómo: ejecutar UNA vez en Workbench, conectado como root, DESPUÉS de la
-- migración 001.
-- =====================================================================
SET NAMES utf8mb4;
USE tesis2026;

-- AFTER password_hash: la ubica al lado de la contraseña, solo por orden.
-- DEFAULT 0: los usuarios que ya existen (por ejemplo, el admin creado por
-- consola) no quedan obligados a cambiarla.
ALTER TABLE usuario
    ADD COLUMN debe_cambiar_clave TINYINT(1) NOT NULL DEFAULT 0 AFTER password_hash;
