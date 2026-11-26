"""
Páginas de error propias, con el mismo diseño que el resto del sistema.

app_errorhandler (a diferencia de errorhandler) atiende el error en TODA la
aplicación, no solo en las rutas de este blueprint.
"""
from flask import Blueprint, render_template

from app.business.permisos import SinPermiso

errores_bp = Blueprint("errores", __name__)


@errores_bp.app_errorhandler(403)
def prohibido(error):
    # El segundo valor del return es el código HTTP de la respuesta.
    return render_template("errores/403.html"), 403


# Cuando un service lanza SinPermiso (por ejemplo, un Jefe de área que
# intenta editar a un usuario de otra área), se responde igual que un 403.
@errores_bp.app_errorhandler(SinPermiso)
def sin_permiso(error):
    return render_template("errores/403.html"), 403


@errores_bp.app_errorhandler(404)
def no_encontrado(error):
    return render_template("errores/404.html"), 404
