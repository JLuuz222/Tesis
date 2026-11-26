"""
Quién puede gestionar a quién (paso 0.3).

Reglas acordadas por el equipo:
  * El Administrador gestiona a todos los usuarios, áreas y puestos.
  * El Jefe de área gestiona solo a los EMPLEADOS de SU área: no puede
    crear ni editar administradores ni otros jefes, ni mover a nadie de área.
  * El Empleado no gestiona usuarios.

Las rutas usan estas funciones para decidir qué mostrar, y los services las
vuelven a usar antes de guardar: aunque alguien arme el pedido a mano, el
permiso se controla igual.
"""
from app.business import roles


class SinPermiso(Exception):
    """El usuario no tiene permiso para esa acción. La ruta responde con 403."""


def puede_gestionar_usuarios(actor) -> bool:
    return actor.tiene_rol(roles.ADMINISTRADOR, roles.JEFE_DE_AREA)


def puede_gestionar_areas(actor) -> bool:
    return actor.tiene_rol(roles.ADMINISTRADOR)


def puede_gestionar_a(actor, usuario) -> bool:
    """¿actor puede editar, dar de baja o restablecer la clave de usuario?"""
    if actor.tiene_rol(roles.ADMINISTRADOR):
        return True
    if actor.tiene_rol(roles.JEFE_DE_AREA):
        return (usuario.id_departamento == actor.id_departamento
                and usuario.rol.nombre == roles.EMPLEADO)
    return False


def exigir(condicion: bool) -> None:
    """Lanza SinPermiso si la condición no se cumple."""
    if not condicion:
        raise SinPermiso()
