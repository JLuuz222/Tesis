"""
Nombres de los roles del sistema.

Están escritos una sola vez acá y el resto del código usa estas constantes.
Si escribiéramos "Jefe de área" a mano en cada archivo, un error de tipeo
("Jefe de area") haría fallar un permiso sin ningún aviso.

Tienen que coincidir con los datos que carga der_v3.sql en la tabla rol.
"""
ADMINISTRADOR = "Administrador"
JEFE_DE_AREA = "Jefe de área"
EMPLEADO = "Empleado"
