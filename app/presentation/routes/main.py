"""
Rutas generales del sistema.

Un Blueprint es un grupo de rutas que después se registra en la app. Hay uno
por área funcional (main, auth y, más adelante, tareas, reportes...), así
cada módulo vive en su propio archivo.
"""
from flask import Blueprint, render_template
from flask_login import login_required

from app.business import roles
from app.business.estado_sistema_service import obtener_estado_base
from app.presentation.decorators import rol_requerido

# "main" es el nombre interno del blueprint. Se usa para armar links:
# url_for("main.inicio") devuelve "/".
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required   # Sin sesión iniciada, Flask-Login redirige a /login.
def inicio():
    return render_template("inicio.html")


# Página de diagnóstico: solo para administradores. Es la página de inicio
# del paso 0.1, ahora protegida por rol.
@main_bp.route("/admin/estado")
@login_required
@rol_requerido(roles.ADMINISTRADOR)
def estado_sistema():
    # La ruta no sabe de SQL: pide el dato al service (capa de negocio)
    # y se lo pasa a la plantilla (capa de presentación).
    estado = obtener_estado_base()
    return render_template("admin/estado.html", estado=estado)
