"""
Gestión de áreas (tabla departamento) y de sus puestos (paso 0.3).

Solo el Administrador gestiona áreas y puestos.
"""
from dataclasses import dataclass

from sqlalchemy import func, select

from app.business import auditoria_service, permisos, roles, validaciones_usuario as v
from app.business.validaciones_usuario import ErrorDeValidacion
from app.data.models import Departamento, Puesto, Rol, Usuario
from app.extensions import db


@dataclass
class DatosArea:
    nombre: str
    codigo: str
    descripcion: str | None = None
    email_contacto: str | None = None
    telefono_contacto: str | None = None
    id_usuario_jefe: int | None = None


# --- Consultas ----------------------------------------------------------------

def listar_con_totales() -> list[tuple[Departamento, int, int]]:
    """Cada área con su cantidad de usuarios activos y de puestos.

    Devuelve tuplas (area, usuarios_activos, puestos). Las cuentas se hacen
    en MySQL con subconsultas, en una sola consulta, en vez de una por área.
    """
    usuarios_activos = (select(func.count()).select_from(Usuario)
                        .where(Usuario.id_departamento == Departamento.id_departamento,
                               Usuario.activo.is_(True))
                        .scalar_subquery())
    puestos = (select(func.count()).select_from(Puesto)
               .where(Puesto.id_departamento == Departamento.id_departamento)
               .scalar_subquery())
    filas = db.session.execute(
        select(Departamento, usuarios_activos, puestos).order_by(Departamento.nombre))
    return [tuple(fila) for fila in filas]


def candidatos_a_jefe(area: Departamento) -> list[Usuario]:
    """Usuarios activos del área con rol Jefe de área."""
    return list(db.session.scalars(
        select(Usuario).join(Usuario.rol)
        .where(Usuario.id_departamento == area.id_departamento,
               Usuario.activo.is_(True), Rol.nombre == roles.JEFE_DE_AREA)
        .order_by(Usuario.apellido)))


# --- Áreas --------------------------------------------------------------------

def _validar_area(datos: DatosArea, area_existente: Departamento | None = None) -> dict:
    limpio = {
        "nombre": v.texto_obligatorio(datos.nombre, "El nombre", 100),
        # El código se guarda en mayúsculas: "com" -> "COM".
        "codigo": v.texto_obligatorio(datos.codigo, "El código", 20).upper(),
        "descripcion": v.texto_opcional(datos.descripcion, "La descripción", 255),
        "telefono_contacto": v.texto_opcional(datos.telefono_contacto, "El teléfono", 20),
        "email_contacto": None,
    }
    # El email de contacto de un área puede ser corporativo, así que acá
    # solo se controla el formato, no la lista de dominios de los usuarios.
    email = v.texto_opcional(datos.email_contacto, "El email de contacto", 100)
    if email:
        limpio["email_contacto"] = v.validar_formato_email(email)

    id_propio = area_existente.id_departamento if area_existente else None
    for columna, valor, texto in ((Departamento.nombre, limpio["nombre"], "ese nombre"),
                                  (Departamento.codigo, limpio["codigo"], "ese código")):
        otra = db.session.scalar(select(Departamento).where(columna == valor))
        if otra and otra.id_departamento != id_propio:
            raise ErrorDeValidacion(f"Ya existe un área con {texto} ({valor}).")

    # El jefe solo se puede elegir al editar: un área nueva todavía no tiene usuarios.
    limpio["id_usuario_jefe"] = None
    if area_existente and datos.id_usuario_jefe:
        if datos.id_usuario_jefe not in {u.id_usuario for u in candidatos_a_jefe(area_existente)}:
            raise ErrorDeValidacion(
                "El jefe tiene que ser un usuario activo del área con rol Jefe de área.")
        limpio["id_usuario_jefe"] = datos.id_usuario_jefe
    return limpio


def crear_area(actor, datos: DatosArea, ip: str | None = None) -> Departamento:
    permisos.exigir(permisos.puede_gestionar_areas(actor))
    area = Departamento(**_validar_area(datos))
    db.session.add(area)
    db.session.flush()
    auditoria_service.registrar("crear", "departamento", id_usuario=actor.id_usuario,
                                id_entidad=area.id_departamento,
                                detalle=f"Alta del área {area.nombre}", ip=ip)
    db.session.commit()
    return area


def actualizar_area(actor, area: Departamento, datos: DatosArea, ip: str | None = None) -> None:
    permisos.exigir(permisos.puede_gestionar_areas(actor))
    limpio = _validar_area(datos, area_existente=area)
    cambios = [campo for campo, valor in limpio.items() if getattr(area, campo) != valor]
    for campo, valor in limpio.items():
        setattr(area, campo, valor)
    auditoria_service.registrar("modificar", "departamento", id_usuario=actor.id_usuario,
                                id_entidad=area.id_departamento,
                                detalle="Cambió: " + (", ".join(cambios) if cambios else "nada"),
                                ip=ip)
    db.session.commit()


def cambiar_estado_area(actor, area: Departamento, activo: bool, ip: str | None = None) -> None:
    """Baja o alta lógica de un área.

    No se puede dar de baja un área con usuarios activos: primero hay que
    pasarlos a otra área o darlos de baja.
    """
    permisos.exigir(permisos.puede_gestionar_areas(actor))
    if not activo:
        activos = db.session.scalar(
            select(func.count()).select_from(Usuario)
            .where(Usuario.id_departamento == area.id_departamento, Usuario.activo.is_(True)))
        if activos:
            raise ErrorDeValidacion(
                f"El área {area.nombre} tiene {activos} usuario(s) activo(s): "
                "pasalos a otra área o dalos de baja primero.")
    area.activo = activo
    auditoria_service.registrar("modificar", "departamento", id_usuario=actor.id_usuario,
                                id_entidad=area.id_departamento,
                                detalle="Alta del área" if activo else "Baja del área", ip=ip)
    db.session.commit()


# --- Puestos ------------------------------------------------------------------

def listar_puestos(area: Departamento) -> list[tuple[Puesto, int]]:
    """Puestos del área con la cantidad de usuarios (activos o no) que lo tienen."""
    usuarios = (select(func.count()).select_from(Usuario)
                .where(Usuario.id_puesto == Puesto.id_puesto).scalar_subquery())
    filas = db.session.execute(
        select(Puesto, usuarios).where(Puesto.id_departamento == area.id_departamento)
        .order_by(Puesto.nombre))
    return [tuple(fila) for fila in filas]


def _validar_puesto(area: Departamento, nombre: str, descripcion: str | None,
                    puesto_existente: Puesto | None = None) -> dict:
    nombre = v.texto_obligatorio(nombre, "El nombre del puesto", 100)
    otro = db.session.scalar(select(Puesto).where(Puesto.id_departamento == area.id_departamento,
                                                  Puesto.nombre == nombre))
    if otro and (puesto_existente is None or otro.id_puesto != puesto_existente.id_puesto):
        raise ErrorDeValidacion(f"El área {area.nombre} ya tiene un puesto llamado {nombre}.")
    return {"nombre": nombre, "descripcion": v.texto_opcional(descripcion, "La descripción", 255)}


def crear_puesto(actor, area: Departamento, nombre: str, descripcion: str | None,
                 ip: str | None = None) -> Puesto:
    permisos.exigir(permisos.puede_gestionar_areas(actor))
    puesto = Puesto(**_validar_puesto(area, nombre, descripcion),
                    id_departamento=area.id_departamento)
    db.session.add(puesto)
    db.session.flush()
    auditoria_service.registrar("crear", "puesto", id_usuario=actor.id_usuario,
                                id_entidad=puesto.id_puesto,
                                detalle=f"Puesto {puesto.nombre} en {area.nombre}", ip=ip)
    db.session.commit()
    return puesto


def actualizar_puesto(actor, puesto: Puesto, nombre: str, descripcion: str | None,
                      ip: str | None = None) -> None:
    permisos.exigir(permisos.puede_gestionar_areas(actor))
    for campo, valor in _validar_puesto(puesto.departamento, nombre, descripcion,
                                        puesto_existente=puesto).items():
        setattr(puesto, campo, valor)
    auditoria_service.registrar("modificar", "puesto", id_usuario=actor.id_usuario,
                                id_entidad=puesto.id_puesto, detalle=f"Puesto {puesto.nombre}",
                                ip=ip)
    db.session.commit()


def eliminar_puesto(actor, puesto: Puesto, ip: str | None = None) -> None:
    """Borra un puesto, solo si ningún usuario lo tiene asignado.

    A diferencia de usuarios y áreas, el puesto se borra de verdad: la
    tabla no tiene columna activo y un puesto sin usuarios no deja historial.
    """
    permisos.exigir(permisos.puede_gestionar_areas(actor))
    en_uso = db.session.scalar(
        select(func.count()).select_from(Usuario).where(Usuario.id_puesto == puesto.id_puesto))
    if en_uso:
        raise ErrorDeValidacion(
            f"El puesto {puesto.nombre} lo tienen {en_uso} usuario(s): cambiales el puesto primero.")
    auditoria_service.registrar("eliminar", "puesto", id_usuario=actor.id_usuario,
                                id_entidad=puesto.id_puesto,
                                detalle=f"Puesto {puesto.nombre} de {puesto.departamento.nombre}",
                                ip=ip)
    db.session.delete(puesto)
    db.session.commit()
