"""
Rutas generales del sistema.

Un Blueprint es un grupo de rutas que después se registra en la app. Más
adelante habrá uno por módulo (auth, tareas, reportes...), así cada módulo
vive en su propio archivo.
"""
from flask import Blueprint, render_template

from app.business.estado_sistema_service import obtener_estado_base

# "main" es el nombre interno del blueprint. Se usa para armar links:
# url_for("main.inicio") devuelve "/".
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def inicio():
    # La ruta no sabe de SQL: pide el dato al service (capa de negocio)
    # y se lo pasa a la plantilla (capa de presentación).
    estado = obtener_estado_base()
    return render_template("inicio.html", estado=estado)
