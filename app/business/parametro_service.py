"""
Lectura de los parámetros configurables (tabla parametro).

Los parámetros permiten cambiar una regla sin tocar el código: por ejemplo,
agregar un dominio de email permitido con un UPDATE en la base.
"""
from app.business.validaciones_usuario import DOMINIOS_POR_DEFECTO
from app.data.models import Parametro
from app.extensions import db


def obtener(clave: str, por_defecto: str | None = None) -> str | None:
    parametro = db.session.get(Parametro, clave)
    return parametro.valor if parametro else por_defecto


def dominios_email_permitidos() -> tuple[str, ...]:
    """Lee el parámetro 'gmail.com,outlook.com,...' y lo convierte en tupla.

    Si el parámetro no existe o está vacío, usa la lista por defecto.
    """
    valor = obtener("dominios_email_permitidos")
    if not valor:
        return DOMINIOS_POR_DEFECTO
    # "gmail.com, Outlook.com" -> ("gmail.com", "outlook.com")
    return tuple(d.strip().lower() for d in valor.split(",") if d.strip())
