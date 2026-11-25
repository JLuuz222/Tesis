"""
Rutas de autenticación: iniciar y cerrar sesión.
"""
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.business import auth_service
from app.presentation.forms import LoginForm

auth_bp = Blueprint("auth", __name__)


def _es_url_interna(url: str | None) -> bool:
    """Evita redirigir a otro sitio después del login.

    Flask-Login agrega ?next=/pagina para volver a donde el usuario quería
    ir. Si alguien arma un link con ?next=https://sitio-falso.com, sin este
    control el sistema mandaría ahí al usuario después de loguearse.
    Solo aceptamos rutas internas: sin dominio, empezando con "/".
    """
    if not url:
        return False
    partes = urlsplit(url)
    return not partes.scheme and not partes.netloc and url.startswith("/")


# methods=["GET", "POST"]: GET muestra el formulario, POST lo recibe.
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.inicio"))

    form = LoginForm()

    # validate_on_submit() es True solo si llegó un POST, el token CSRF es
    # válido y todos los campos pasan sus validaciones.
    if form.validate_on_submit():
        usuario = auth_service.autenticar(form.email.data, form.clave.data, request.remote_addr)
        if usuario:
            # login_user guarda el id del usuario en la cookie de sesión.
            # remember=True además deja una cookie que dura días.
            login_user(usuario, remember=form.recordarme.data)
            destino = request.args.get("next")
            return redirect(destino if _es_url_interna(destino) else url_for("main.inicio"))

        # El mismo mensaje para email inexistente y para clave incorrecta:
        # así nadie puede averiguar qué emails están registrados.
        flash("Email o contraseña incorrectos.", "danger")

    return render_template("auth/login.html", form=form)


# Cerrar sesión por POST (con token CSRF) y no por un simple link: un link
# podría estar escondido en otra página y cerrarle la sesión a alguien.
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    auth_service.registrar_logout(current_user, request.remote_addr)
    logout_user()
    flash("Cerraste sesión.", "info")
    return redirect(url_for("auth.login"))
