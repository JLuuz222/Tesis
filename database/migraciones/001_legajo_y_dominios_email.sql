-- =====================================================================
-- Migración 001: reglas de negocio de usuarios
--
--   1. numero_legajo pasa de INT a CHAR(5) para guardar los ceros a la
--      izquierda ("00005"). Un INT no los guarda: para MySQL, 5 y 00005
--      son el mismo número.
--   2. Se agrega un CHECK: el legajo tiene que ser exactamente 5 dígitos
--      y distinto de "00000".
--   3. Se agrega el parámetro dominios_email_permitidos.
--
-- Para quién: bases creadas con la versión ANTERIOR de der_v3.sql. Una
-- base nueva creada con el der_v3.sql actual ya incluye estos cambios.
--
-- Cómo: ejecutar UNA vez en Workbench, conectado como root (tesis_app no
-- tiene permiso para cambiar la estructura de las tablas).
-- =====================================================================
SET NAMES utf8mb4;
USE tesis2026;

-- MODIFY COLUMN cambia el tipo. Si ya hay legajos cargados, MySQL convierte
-- el número a texto (5 -> '5'); el UPDATE de abajo le agrega los ceros.
ALTER TABLE usuario MODIFY COLUMN numero_legajo CHAR(5) NOT NULL;

-- LPAD(texto, 5, '0') completa con ceros a la izquierda hasta 5 caracteres.
-- WHERE con la clave primaria: en Workbench, el "safe update mode" rechaza
-- UPDATE sin una condición sobre una clave.
UPDATE usuario SET numero_legajo = LPAD(numero_legajo, 5, '0') WHERE id_usuario > 0;

ALTER TABLE usuario
    ADD CONSTRAINT ck_usuario_legajo
        CHECK (numero_legajo REGEXP '^[0-9]{5}$' AND numero_legajo <> '00000');

-- INSERT IGNORE: si el parámetro ya existe, no hace nada (no da error).
INSERT IGNORE INTO parametro (clave, valor, descripcion) VALUES
    ('dominios_email_permitidos',
     'gmail.com,gmail.com.ar,outlook.com,outlook.com.ar,hotmail.com,hotmail.com.ar,yahoo.com,yahoo.com.ar',
     'Dominios de email aceptados al crear usuarios, separados por coma');
