"""
Registro de auditoría: guarda en la tabla auditoria quién hizo qué.

Cualquier módulo que necesite dejar constancia de una acción llama a
registrar(). Por ahora lo usa el login; más adelante, tareas y manuales.
"""
from app.data.models import Auditoria
from app.extensions import db


def registrar(accion: str, entidad: str, id_usuario: int | None = None,
              id_entidad: int | None = None, detalle: str | None = None,
              ip: str | None = None) -> None:
    """Agrega un registro de auditoría a la sesión actual.

    No hace commit: el registro se guarda junto con el resto de los cambios
    de la operación. Así, si la operación falla, tampoco queda un registro
    de algo que en realidad no pasó.
    """
    db.session.add(Auditoria(
        id_usuario=id_usuario,
        accion=accion,
        entidad=entidad,
        id_entidad=id_entidad,
        # [:500] recorta el texto al largo máximo de la columna.
        detalle=detalle[:500] if detalle else None,
        ip=ip,
    ))
