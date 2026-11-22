"""
Service de diagnóstico: comprueba que la aplicación llegue a la base.

Es el primer ejemplo de la capa de negocio. La ruta no habla con la base
directamente: le pide el dato a este service.
"""
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.data.models import Rol
from app.extensions import db


def obtener_estado_base() -> dict:
    """Devuelve si la conexión anda, la versión de MySQL y los roles cargados.

    Nunca lanza una excepción: si la base no responde, devuelve el error
    como texto para mostrarlo en pantalla.
    """
    try:
        # text() envía SQL escrito a mano. Lo usamos solo para pedir la versión.
        version = db.session.execute(text("SELECT VERSION()")).scalar_one()

        # select(Rol) es la forma de SQLAlchemy 2.0 de escribir
        # "SELECT * FROM rol ORDER BY id_rol". scalars() devuelve objetos Rol.
        roles = db.session.scalars(select(Rol).order_by(Rol.id_rol)).all()

        return {"conectado": True, "version": version, "roles": roles, "error": None}
    except SQLAlchemyError as error:
        # Si falla la conexión, la sesión queda en estado de error; rollback()
        # la limpia para que el próximo pedido funcione.
        db.session.rollback()
        return {"conectado": False, "version": None, "roles": [], "error": str(error.orig or error)}
