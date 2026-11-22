-- =====================================================================
-- Crea el usuario de MySQL que usa la aplicación.
--
-- Por qué no usar root: root puede hacer cualquier cosa en todo el
-- servidor (borrar bases, crear usuarios). Si su contraseña se filtra
-- desde el .env, se compromete todo. tesis_app solo puede leer y escribir
-- datos en tesis2026, y nada más.
--
-- Cómo usarlo: ejecutarlo UNA vez en Workbench conectado como root,
-- después de reemplazar la contraseña. Esa misma contraseña va en el .env
-- (DB_PASSWORD).
-- =====================================================================

CREATE USER IF NOT EXISTS 'tesis_app'@'localhost'
    IDENTIFIED BY 'CAMBIAR_ESTA_CLAVE';

-- SELECT, INSERT, UPDATE, DELETE: leer y modificar datos.
-- No le damos CREATE, DROP ni ALTER: la estructura la cambiamos nosotros
-- con los scripts, no la aplicación.
GRANT SELECT, INSERT, UPDATE, DELETE ON tesis2026.* TO 'tesis_app'@'localhost';

FLUSH PRIVILEGES;
