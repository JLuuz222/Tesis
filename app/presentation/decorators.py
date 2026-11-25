"""
Decoradores de la capa de presentación.

Un decorador es una función que "envuelve" a otra para agregarle algo antes
de que se ejecute. Se escribe con @ arriba de la ruta:

    @main_bp.route("/admin")
    @login_required                         # 1) tiene que haber iniciado sesión
    @rol_requerido(roles.ADMINISTRADOR)     # 2) y tener este rol
    def panel_admin(): ...

Los decoradores se aplican de abajo hacia arriba, pero se ejecutan de
arriba hacia abajo: primero se verifica la sesión y después el rol.
"""
from functools import wraps

from flask import abort
from flask_login import current_user


def rol_requerido(*nombres_rol: str):
    """Deja pasar solo a los usuarios que tienen alguno de esos roles.

    Si el usuario no tiene el rol, responde 403 (prohibido). Se usa siempre
    debajo de @login_required, que ya garantiza que hay un usuario.
    """
    def decorador(vista):
        # @wraps conserva el nombre de la función original. Flask lo usa
        # para identificar cada ruta; sin esto, dos rutas protegidas
        # chocarían porque las dos se llamarían "envoltura".
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if not current_user.tiene_rol(*nombres_rol):
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador
